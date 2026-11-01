"""
Представления (views) приложения testing — проверка знаний и документы.

Справочники и документы:
  - TestCategoryListView            — список направлений тестирования
  - UserCertificateListCreateView   — список и загрузка документов
  - UserCertificateDetailView       — просмотр, правка, удаление документа
  - PDFProxyView                    — выдача файла документа без ошибок CORS
  - AvailableResumesView            — резюме, по которым можно составить тест

Прохождение теста (порядок вызовов фронтендом):
  1. TestStatusView    — можно ли начать тест
  2. StartTestView     — ИИ генерирует вопросы, создаётся сессия
  3. GetQuestionView   — выдача очередного вопроса
  4. SubmitAnswerView  — сохранение ответа (повторяется для каждого вопроса)
  5. CompleteTestView  — подсчёт результата
  6. TestResultView / TestHistoryView — результаты и история попыток

Примечание: подсчёт баллов намеренно вынесен не сюда, а в модель
TestSession.calculate_score() — ближе к данным, с которыми он работает.
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
import random
import json
from django.http import HttpResponse
import requests
from .models import TestCategory, TestQuestion, UserCertificate, TestSession
from .serializers import (
    TestCategorySerializer, TestQuestionSerializer, UserCertificateSerializer,
    TestSessionSerializer, StartTestSerializer, SubmitAnswerSerializer,
    CompleteTestSerializer, TestResultSerializer
)


class TestCategoryListView(generics.ListAPIView):
    """Список категорий тестов"""

    queryset = TestCategory.objects.all()
    serializer_class = TestCategorySerializer
    # AllowAny — список направлений можно показать и неавторизованному
    # посетителю, личных данных здесь нет
    permission_classes = [permissions.AllowAny]


class UserCertificateListCreateView(generics.ListCreateAPIView):
    """Список и создание сертификатов пользователя"""

    serializer_class = UserCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Парсеры для загрузки файлов (сканов документов)
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Только документы текущего пользователя — чужие недоступны
        return UserCertificate.objects.filter(user=self.request.user).order_by('-issue_date')

    def perform_create(self, serializer):
        # Владелец подставляется из токена, а не из запроса: иначе можно
        # было бы добавить документ другому пользователю
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора"""
        # request нужен сериализатору, чтобы собрать полную ссылку на файл
        # (http://localhost:8000/media/... вместо просто /media/...)
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class UserCertificateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление сертификата"""

    serializer_class = UserCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return UserCertificate.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class TestStatusView(APIView):
    """Статус тестирования пользователя"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Собирает всё, что нужно главной странице тестирования:
        результат прошлой попытки, наличие незавершённого теста,
        доступные категории и количество документов.
        """
        # Последний завершённый тест — из него берём прошлый результат
        last_session = TestSession.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-completed_at').first()

        # Незавершённый тест: если он есть, пользователю предлагают его продолжить
        active_session = TestSession.objects.filter(
            user=request.user,
            status='in_progress'
        ).first()

        certificates = UserCertificate.objects.filter(user=request.user)
        categories = TestCategory.objects.all()

        # Базовый ответ: значения по умолчанию для нового пользователя
        response_data = {
            'has_active_test': active_session is not None,
            'can_start_new_test': True,
            'next_retake_date': None,
            'last_score': None,
            'last_session': None,
            'certificates_count': certificates.count(),
            'categories': TestCategorySerializer(categories, many=True).data
        }

        # Если тесты уже проходились, уточняем данные
        if last_session:
            response_data.update({
                'last_score': last_session.score,
                'last_session': TestSessionSerializer(last_session).data,
                # can_start_test() — метод модели: учитывает проходной балл
                # и дату, когда откроется пересдача
                'can_start_new_test': last_session.can_start_test(),
                'next_retake_date': last_session.next_retake_date
            })

        if active_session:
            response_data.update({
                'active_session': TestSessionSerializer(active_session).data
            })

        return Response(response_data)


class StartTestView(APIView):
    """
    Начать новый тест с AI-генерацией вопросов на основе резюме.
    POST /api/testing/start/

    Порядок работы:
      1. Проверить, что нет незавершённого теста
      2. Взять последнее резюме пользователя
      3. Определить специализацию и опыт по тексту резюме
      4. Попросить ИИ сгенерировать вопросы под эти навыки
      5. Если ИИ не справился — добрать вопросы из базы
      6. Создать сессию тестирования
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print(f"=== НАЧАЛО ТЕСТИРОВАНИЯ ===")
        print(f"Пользователь: {request.user.email}")
        print(f"Данные запроса: {request.data}")

        # Используем упрощенный сериализатор
        category_id = request.data.get('category_id')
        # По умолчанию 10 вопросов, если фронтенд не указал другое число
        question_count = request.data.get('question_count', 10)

        try:
            # Проверяем активный тест
            # Запрет на два теста одновременно: иначе ответы одной
            # попытки попали бы в другую
            active_session = TestSession.objects.filter(
                user=request.user,
                status='in_progress'
            ).first()

            if active_session:
                return Response({
                    'error': 'У вас уже есть активный тест',
                    'session_id': active_session.id
                }, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, есть ли у пользователя резюме
            # Импорт внутри метода, а не сверху файла — так исключается
            # циклический импорт между приложениями testing и resumes
            from resumes.models import Resume
            resume = Resume.objects.filter(
                user=request.user
            ).order_by('-upload_date').first()

            # Без резюме тест составить нельзя: вопросы строятся по его тексту
            if not resume:
                return Response({
                    'error': 'У вас нет загруженного резюме. Пожалуйста, загрузите резюме в разделе "Мои резюме" сначала.'
                }, status=status.HTTP_400_BAD_REQUEST)

            print(f"Найдено резюме: {resume.id} - {resume.original_filename}")

            # Определяем категорию на основе специализации из резюме
            category = None
            if category_id:
                try:
                    category = TestCategory.objects.get(id=category_id)
                except TestCategory.DoesNotExist:
                    # Неверный id категории не должен прерывать тест —
                    # ниже подставится категория по умолчанию
                    category = None

            # Если категория не указана, создаем/получаем категорию по умолчанию
            if not category:
                category, _ = TestCategory.objects.get_or_create(
                    name='Frontend Development',
                    defaults={'description': 'Тестирование для Frontend разработчиков (React, JavaScript, TypeScript, CSS)'}
                )

            # Здесь будут собраны id вопросов для этой сессии
            questions_data = []

            # Генерация AI-вопросов на основе резюме
            print("Пытаемся сгенерировать AI-вопросы из резюме...")

            try:
                from core.services.claude_service import ClaudeService
                ai_service = ClaudeService()

                # Получаем текст резюме
                # or "" защищает от None, если текст не извлёкся
                resume_text = resume.extracted_text or ""

                # Короткий текст не даёт ИИ достаточно информации
                if resume_text and len(resume_text) > 50:
                    # Определяем специализацию из резюме
                    specialization = self._detect_specialization(resume_text)
                    print(f"Определенная специализация: {specialization}")

                    # Определяем уровень опыта
                    experience = self._detect_experience(resume_text)
                    print(f"Определенный опыт: {experience} лет")

                    # Генерируем вопросы через Claude
                    # Сложность вычисляется из стажа: новичку — простые вопросы
                    ai_questions = ai_service.generate_test_questions(
                        resume_text,
                        specialization,
                        self._map_experience_to_difficulty(experience),
                        question_count
                    )

                    print(f"Сгенерировано AI-вопросов: {len(ai_questions)}")

                    # Сохраняем AI-вопросы как временные
                    for q_data in ai_questions:
                        try:
                            question = TestQuestion.objects.create(
                                category=category,
                                # Срезы [:500] не дают превысить длину поля в БД
                                question_text=q_data['question_text'][:500],
                                question_type=q_data['question_type'],
                                options=q_data.get('options', []),
                                # Список правильных ответов сохраняем JSON-строкой,
                                # так как поле в модели текстовое
                                correct_answer=json.dumps(q_data['correct_answer']) if isinstance(q_data['correct_answer'], list) else str(q_data['correct_answer']),
                                explanation=q_data.get('explanation', '')[:500],
                                difficulty=q_data.get('difficulty', 3),
                                time_limit_seconds=90,
                                # is_temporary=True — вопрос создан под конкретное
                                # резюме и позже удаляется командой cleanup_temp_questions
                                is_temporary=True
                            )
                            questions_data.append(question.id)
                            print(f"Создан вопрос: {question.id}")
                        except Exception as e:
                            # Один некорректный вопрос не должен ломать весь тест
                            print(f"Ошибка сохранения вопроса: {e}")
                            continue

                    # Если AI не сгенерировал достаточно вопросов, добавляем из базы
                    if len(questions_data) < question_count:
                        additional_needed = question_count - len(questions_data)
                        additional_questions = self._get_questions_from_db(category, additional_needed)
                        questions_data.extend(additional_questions)
                        print(f"Добавлено {len(additional_questions)} вопросов из базы")

                else:
                    print("Текст резюме слишком короткий, используем вопросы из базы")
                    questions_data = self._get_questions_from_db(category, question_count)

            except Exception as e:
                print(f"Ошибка AI-генерации вопросов: {e}")
                import traceback
                traceback.print_exc()
                # Если AI не сработал, используем вопросы из базы
                # Благодаря этому тест доступен даже без работающего ИИ
                questions_data = self._get_questions_from_db(category, question_count)

            print(f"Всего вопросов подготовлено: {len(questions_data)}")

            # Тест из 1-2 вопросов не имеет смысла: порог достоверности
            if len(questions_data) < 5:  # Минимум 5 вопросов
                return Response({
                    'error': f'Недостаточно вопросов. Доступно: {len(questions_data)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Создаем сессию тестирования
            # Список вопросов фиксируется здесь: при перезагрузке страницы
            # пользователь получит те же вопросы, а не новые
            session = TestSession.objects.create(
                user=request.user,
                category=category,
                # min() на случай, если вопросов набралось меньше запрошенного
                total_questions=min(len(questions_data), question_count),
                questions=questions_data[:question_count],
                status='in_progress',
                started_at=timezone.now(),
                is_ai_generated=len(questions_data) > 0
            )

            print(f"=== СОЗДАНА СЕССИЯ ТЕСТИРОВАНИЯ ===")
            print(f"ID сессии: {session.id}")
            print(f"Количество вопросов: {session.total_questions}")
            print(f"AI-генерация: {session.is_ai_generated}")

            return Response({
                'id': session.id,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                } if category else None,
                'total_questions': session.total_questions,
                'status': session.status,
                'started_at': session.started_at,
                'is_ai_generated': session.is_ai_generated
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Общая ошибка в StartTestView: {e}")
            import traceback
            # traceback.print_exc() печатает полный путь ошибки в консоль сервера —
            # помогает найти причину при отладке
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _detect_specialization(self, resume_text):
        """Определяем специализацию из текста резюме"""
        # Простой анализ по ключевым словам (без ИИ): ищем названия
        # технологий в тексте. Результат передаётся ИИ как категория теста
        resume_text_lower = resume_text.lower()

        # Проверяем технологии
        # any(...) — True, если хотя бы одна технология упомянута.
        # Порядок проверок задаёт приоритет: сначала frontend, затем backend и т.д.
        if any(tech in resume_text_lower for tech in ['react', 'angular', 'vue', 'javascript', 'typescript']):
            return 'frontend'
        elif any(tech in resume_text_lower for tech in ['python', 'django', 'flask', 'java', 'spring']):
            return 'backend'
        elif any(tech in resume_text_lower for tech in ['sql', 'database', 'postgresql', 'mysql']):
            return 'database'
        elif any(tech in resume_text_lower for tech in ['devops', 'docker', 'kubernetes', 'aws']):
            return 'devops'
        elif any(tech in resume_text_lower for tech in ['data', 'machine learning', 'ai', 'pandas']):
            return 'data_science'

        # Ничего не нашли — общие профессиональные вопросы
        return 'general'

    def _detect_experience(self, resume_text):
        """Определяем опыт из резюме"""
        import re   # регулярные выражения

        # Ищем упоминания опыта
        # Шаблоны описывают разные формулировки стажа в резюме.
        # \d+ — число, \s* — любое количество пробелов, [а]? — буква «а» необязательна
        experience_patterns = [
            r'(\d+)\s*год[а]?\s+опыт[а]?',      # "3 года опыта"
            r'опыт\s+работы\s+(\d+)',            # "опыт работы 3"
            r'(\d+)\s*лет\s+в\s+разработке',     # "5 лет в разработке"
            r'(\d+)\s*год[а]?\s+в\s+it'          # "2 года в IT"
        ]

        for pattern in experience_patterns:
            match = re.search(pattern, resume_text.lower())
            if match:
                try:
                    # group(1) — число в круглых скобках шаблона
                    return int(match.group(1))
                except:
                    continue

        return 1  # По умолчанию 1 год

    def _map_experience_to_difficulty(self, experience_years):
        """Маппим опыт на уровень сложности"""
        # Чем больше стаж, тем сложнее вопросы
        if experience_years < 1:
            return 'easy'      # Junior
        elif experience_years < 3:
            return 'medium'    # Middle
        else:
            return 'hard'      # Senior

    def _get_questions_from_db(self, category, question_count):
        """Получить вопросы из базы данных"""
        # Запасной источник вопросов, когда ИИ недоступен
        # или сгенерировал слишком мало вопросов
        try:
            if category:
                questions = TestQuestion.objects.filter(
                    category=category,
                    is_active=True,
                    # Берём только постоянные вопросы: временные созданы
                    # под чужие резюме и этому пользователю не подходят
                    is_temporary=False
                )
            else:
                questions = TestQuestion.objects.filter(
                    is_active=True,
                    is_temporary=False
                )

            # Берем случайные вопросы
            # order_by('?') — случайный порядок: при пересдаче
            # пользователь получит другой набор вопросов
            questions = questions.order_by('?')[:question_count]
            return [q.id for q in questions]

        except Exception as e:
            print(f"Ошибка получения вопросов из базы: {e}")
            # Пустой список: вызывающий код сообщит «недостаточно вопросов»
            return []


class GetQuestionView(APIView):
    """Получить следующий вопрос теста"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        """
        Выдаёт первый вопрос, на который пользователь ещё не ответил.

        Такой подход вместо хранения «номера текущего вопроса» позволяет
        продолжить тест с нужного места после перезагрузки страницы.
        """
        # status='in_progress' в условии: получить вопрос
        # из завершённого или чужого теста невозможно
        session = get_object_or_404(
            TestSession,
            id=session_id,
            user=request.user,
            status='in_progress'
        )

        # Находим неотвеченные вопросы
        # Ключи user_answers — это id вопросов, на которые ответ уже есть.
        # str(q) нужен потому, что в JSON ключи всегда строки, а в
        # session.questions id хранятся числами
        answered_questions = list(session.user_answers.keys())
        remaining_questions = [q for q in session.questions if str(q) not in answered_questions]

        # Вопросы закончились — фронтенд по признаку completed
        # перейдёт к завершению теста
        if not remaining_questions:
            return Response({
                'message': 'Все вопросы уже отвечены',
                'completed': True
            })

        # Берем первый неотвеченный вопрос
        question_id = remaining_questions[0]
        question = get_object_or_404(TestQuestion, id=question_id)

        # Сериализатор намеренно НЕ отдаёт поле correct_answer —
        # иначе правильный ответ был бы виден в коде страницы
        question_data = TestQuestionSerializer(question).data

        # Добавляем прогресс
        # Данные для полосы прогресса и таймера на экране
        progress = {
            'current': len(answered_questions) + 1,
            'total': session.total_questions,
            'remaining_time': session.get_remaining_time()
        }

        return Response({
            'question': question_data,
            'progress': progress,
            'session_id': session.id
        })


class SubmitAnswerView(APIView):
    """Отправить ответ на вопрос"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Сохраняет ответ пользователя на один вопрос.

        Правильность здесь НЕ проверяется — только сохранение. Проверка
        выполняется один раз в конце, в CompleteTestView, чтобы по ответу
        сервера нельзя было узнать правильный вариант во время теста.
        """
        serializer = SubmitAnswerSerializer(data=request.data)
        if serializer.is_valid():
            session = get_object_or_404(
                TestSession,
                id=serializer.validated_data['session_id'],
                user=request.user,
                status='in_progress'
            )

            # Ключ приводим к строке: так требует формат JSON
            question_id = str(serializer.validated_data['question_id'])

            # Проверяем, что вопрос входит в тест
            # Защита от подмены: нельзя отправить ответ на вопрос,
            # который не выдавался в этой сессии
            if int(question_id) not in session.questions:
                return Response(
                    {'error': 'Вопрос не входит в этот тест'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Сохраняем ответ
            # .copy() обязателен: Django не замечает изменений
            # внутри JSONField, если менять словарь напрямую
            user_answers = session.user_answers.copy()
            user_answers[question_id] = serializer.validated_data['answer']
            session.user_answers = user_answers

            # Обновляем потраченное время
            if session.started_at:
                time_spent = (timezone.now() - session.started_at).total_seconds()
                session.time_spent_seconds = int(time_spent)

            session.save()

            return Response({
                'success': True,
                'session_id': session.id
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteTestView(APIView):
    """Завершить тест и получить результаты"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print(f"=== ЗАВЕРШЕНИЕ ТЕСТА ===")

        serializer = CompleteTestSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"Ошибки валидации: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            session_id = serializer.validated_data['session_id']

            # Здесь status не указан: завершать можно и сессию,
            # у которой вышло время
            session = get_object_or_404(
                TestSession,
                id=session_id,
                user=request.user
            )

            print(f"Сессия найдена: {session.id}, статус: {session.status}")

            # Защита от повторного подсчёта: иначе можно было бы
            # завершить тест дважды и перезаписать результат
            if session.status == 'completed':
                return Response(
                    {'error': 'Тест уже завершен'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Рассчитываем результаты
            # Вся логика проверки ответов — в модели TestSession
            print("Рассчитываем результаты...")
            score = session.calculate_score()

            session.status = 'completed'
            session.completed_at = timezone.now()

            # Обновляем время
            # Итоговое время считаем точно: от начала до завершения
            if session.started_at:
                time_spent = (session.completed_at - session.started_at).total_seconds()
                session.time_spent_seconds = int(time_spent)

            session.save()

            print(f"Результаты: {session.score}%, правильных: {session.correct_count}")

            # Сериализуем результаты
            result_serializer = TestResultSerializer(session)

            return Response({
                'success': True,
                'results': result_serializer.data,
                # Сравнение с проходным баллом (по умолчанию 70%)
                'passed': session.score >= session.passing_score if session.score else False,
                'message': 'Поздравляем! Вы успешно прошли тест.' if session.score >= session.passing_score else 'К сожалению, вы не прошли тест. Попробуйте снова через 7 дней.',
                'score': session.score,
                'correct_count': session.correct_count,
                'incorrect_count': session.incorrect_count,
                'total_questions': session.total_questions,
                # Подробный разбор: какой вопрос, что ответил, как правильно
                'detailed_results': session.detailed_results
            })

        except Exception as e:
            print(f"Ошибка в CompleteTestView: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestResultView(generics.RetrieveAPIView):
    """Получить результаты завершенного теста"""

    serializer_class = TestResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только свои и только завершённые тесты:
        # у незавершённого результата ещё нет
        return TestSession.objects.filter(
            user=self.request.user,
            status='completed'
        )


class TestHistoryView(generics.ListAPIView):
    """История тестирований пользователя"""

    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Все пройденные попытки, свежие сверху
        return TestSession.objects.filter(
            user=self.request.user,
            status='completed'
        ).order_by('-completed_at')


class SessionStatusView(APIView):
    """Проверить статус генерации вопросов"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        """
        Короткая сводка о состоянии сессии.

        Фронтенд обращается сюда, чтобы узнать, готовы ли вопросы,
        и показать индикатор ожидания.
        """
        session = get_object_or_404(
            TestSession,
            id=session_id,
            user=request.user
        )

        return Response({
            'id': session.id,
            'status': session.status,
            'questions_ready': session.status == 'in_progress',
            # Проверка на пустой список: без неё len(None) вызвал бы ошибку
            'questions_count': len(session.questions) if session.questions else 0,
            'total_questions': session.total_questions,
            'is_ai_generated': session.is_ai_generated,
            'category': {
                # Категорию могли удалить (в модели стоит SET_NULL),
                # поэтому проверяем её наличие
                'id': session.category.id if session.category else None,
                'name': session.category.name if session.category else None
            },
            'started_at': session.started_at
        })


class AvailableResumesView(APIView):
    """Получить список резюме пользователя для выбора"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Локальный импорт — чтобы избежать циклического импорта приложений
        from resumes.models import Resume

        resumes = Resume.objects.filter(
            user=request.user
        ).order_by('-upload_date')

        # Словари собираются вручную, а не сериализатором: в списке
        # для выбора нужны только краткие данные и короткий фрагмент текста
        resumes_data = []
        for resume in resumes:
            resumes_data.append({
                'id': resume.id,
                'title': resume.original_filename,
                'upload_date': resume.upload_date,
                'status': resume.status,
                'overall_score': resume.overall_score,
                'analyzed_at': resume.analyzed_at,
                # Первые 100 символов для предпросмотра
                'preview': (resume.extracted_text or "")[:100] + "..." if resume.extracted_text else ""
            })

        return Response(resumes_data)


class PDFProxyView(APIView):
    """Proxy для PDF файлов чтобы обойти CORS"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, document_id):
        """
        Отдаёт файл документа через Django.

        Нужен потому, что встроенный просмотрщик PDF в браузере
        блокируется политикой CORS при обращении к файлу напрямую.
        Заодно проверяется, что документ принадлежит пользователю.
        """
        document = get_object_or_404(
            UserCertificate,
            id=document_id,
            user=request.user
        )

        if document.document_file:
            # Открываем файл локально
            # 'rb' — чтение в двоичном режиме (PDF не является текстом)
            with open(document.document_file.path, 'rb') as f:
                pdf_data = f.read()

            response = HttpResponse(pdf_data, content_type='application/pdf')
            # inline — открыть в браузере, а не скачать файлом
            response['Content-Disposition'] = f'inline; filename="{document.title}.pdf"'
            response['Access-Control-Allow-Origin'] = '*'
            return response

        return Response(
            {'error': 'Файл не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
