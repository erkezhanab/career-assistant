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
    permission_classes = [permissions.AllowAny]


class UserCertificateListCreateView(generics.ListCreateAPIView):
    """Список и создание сертификатов пользователя"""
    serializer_class = UserCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return UserCertificate.objects.filter(user=self.request.user).order_by('-issue_date')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора"""
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
        last_session = TestSession.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-completed_at').first()
        
        active_session = TestSession.objects.filter(
            user=request.user,
            status='in_progress'
        ).first()
        
        certificates = UserCertificate.objects.filter(user=request.user)
        categories = TestCategory.objects.all()
        
        response_data = {
            'has_active_test': active_session is not None,
            'can_start_new_test': True,
            'next_retake_date': None,
            'last_score': None,
            'last_session': None,
            'certificates_count': certificates.count(),
            'categories': TestCategorySerializer(categories, many=True).data
        }
        
        if last_session:
            response_data.update({
                'last_score': last_session.score,
                'last_session': TestSessionSerializer(last_session).data,
                'can_start_new_test': last_session.can_start_test(),
                'next_retake_date': last_session.next_retake_date
            })
        
        if active_session:
            response_data.update({
                'active_session': TestSessionSerializer(active_session).data
            })
        
        return Response(response_data)


class StartTestView(APIView):
    """Начать новый тест с AI-генерацией вопросов на основе выбранного резюме"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        print(f"=== НАЧАЛО ТЕСТИРОВАНИЯ ===")
        print(f"Пользователь: {request.user.email}")
        print(f"Данные запроса: {request.data}")
        
        try:
            resume_id = request.data.get('resume_id')
            category_id = request.data.get('category_id')
            question_count = request.data.get('question_count', 10)
            
            # Проверяем активный тест
            active_session = TestSession.objects.filter(
                user=request.user,
                status='in_progress'
            ).first()
            
            if active_session:
                return Response({
                    'error': 'У вас уже есть активный тест',
                    'session_id': active_session.id,
                    'continue_url': f'/testing/session/{active_session.id}/'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем все резюме пользователя
            from resumes.models import Resume
            user_resumes = Resume.objects.filter(user=request.user).order_by('-upload_date')
            
            if not user_resumes.exists():
                return Response({
                    'error': 'У вас нет загруженных резюме. Пожалуйста, загрузите резюме в разделе "Мои резюме" сначала.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Выбираем резюме
            if resume_id:
                resume = user_resumes.filter(id=resume_id).first()
                if not resume:
                    return Response({
                        'error': 'Указанное резюме не найдено',
                        'available_resumes': [
                            {'id': r.id, 'title': r.original_filename, 'upload_date': r.upload_date}
                            for r in user_resumes
                        ]
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Берем последнее резюме
                resume = user_resumes.first()
            
            print(f"Выбрано резюме: {resume.id} - {resume.original_filename}")
            
            # Определяем категорию
            category = None
            if category_id:
                try:
                    category = TestCategory.objects.get(id=category_id)
                except TestCategory.DoesNotExist:
                    category = None
            
            # Если категория не указана, создаем/получаем категорию на основе специализации
            if not category:
                specialization = self._detect_specialization(resume.extracted_text or "")
                category_name = self._map_specialization_to_category(specialization)
                
                category, _ = TestCategory.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'Тестирование для {category_name}'}
                )
            
            # Создаем сессию сразу, но со статусом "генерация"
            session = TestSession.objects.create(
                user=request.user,
                category=category,
                total_questions=question_count,
                status='generating',  # Новый статус - генерация вопросов
                started_at=timezone.now(),
                selected_resume_id=resume.id
            )
            
            # Запускаем фоновую задачу для генерации вопросов
            self._generate_questions_background(session.id, resume.id, category.id, question_count)
            
            print(f"=== СОЗДАНА СЕССИЯ ТЕСТИРОВАНИЯ ===")
            print(f"ID сессии: {session.id}")
            print(f"Резюме: {resume.original_filename}")
            print(f"Категория: {category.name}")
            print(f"Статус: {session.status}")
            
            return Response({
                'id': session.id,
                'status': session.status,
                'generating': True,
                'message': 'Вопросы генерируются на основе вашего резюме...',
                'estimated_time': '30-60 секунд',
                'resume': {
                    'id': resume.id,
                    'title': resume.original_filename,
                    'upload_date': resume.upload_date
                },
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                },
                'check_status_url': f'/api/testing/session/{session.id}/status/'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Общая ошибка в StartTestView: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_questions_background(self, session_id, resume_id, category_id, question_count):
        """Фоновая генерация вопросов"""
        import threading
        from django.utils import timezone
        
        def generate():
            try:
                from resumes.models import Resume
                from core.services.gemini_service import GeminiService
                
                session = TestSession.objects.get(id=session_id)
                resume = Resume.objects.get(id=resume_id)
                category = TestCategory.objects.get(id=category_id)
                
                print(f"Начинаем генерацию вопросов для сессии {session_id}...")
                
                questions_data = []
                resume_text = resume.extracted_text or ""
                
                if resume_text and len(resume_text) > 100:
                    # Генерация через Gemini
                    gemini = GeminiService()
                    
                    # Определяем специализацию и опыт
                    specialization = self._detect_specialization(resume_text)
                    experience = self._detect_experience(resume_text)
                    difficulty = self._map_experience_to_difficulty(experience)
                    
                    print(f"Генерация вопросов: {specialization}, опыт: {experience} лет, сложность: {difficulty}")
                    
                    ai_questions = gemini.generate_test_questions(
                        resume_text,
                        specialization,
                        difficulty,
                        question_count
                    )
                    
                    print(f"Сгенерировано AI-вопросов: {len(ai_questions)}")
                    
                    # Сохраняем AI-вопросы
                    for q_data in ai_questions:
                        try:
                            question = TestQuestion.objects.create(
                                category=category,
                                question_text=q_data['question_text'][:500],
                                question_type=q_data['question_type'],
                                options=q_data.get('options', []),
                                correct_answer=json.dumps(q_data['correct_answer']) 
                                    if isinstance(q_data['correct_answer'], list) 
                                    else str(q_data['correct_answer']),
                                explanation=q_data.get('explanation', '')[:500],
                                difficulty=q_data.get('difficulty', 3),
                                time_limit_seconds=90,
                                is_temporary=True,
                                generated_from_resume=resume.id
                            )
                            questions_data.append(question.id)
                        except Exception as e:
                            print(f"Ошибка сохранения вопроса: {e}")
                            continue
                
                # Добавляем вопросы из базы, если нужно
                if len(questions_data) < question_count:
                    additional_needed = question_count - len(questions_data)
                    additional_questions = self._get_questions_from_db(category, additional_needed)
                    questions_data.extend(additional_questions)
                
                # Обновляем сессию
                session.questions = questions_data[:question_count]
                session.total_questions = len(session.questions)
                session.status = 'in_progress'
                session.is_ai_generated = len(ai_questions) > 0 if 'ai_questions' in locals() else False
                session.save()
                
                print(f"Генерация завершена для сессии {session_id}. Вопросов: {len(questions_data)}")
                
            except Exception as e:
                print(f"Ошибка генерации вопросов: {e}")
                import traceback
                traceback.print_exc()
                
                # В случае ошибки ставим стандартные вопросы
                try:
                    session = TestSession.objects.get(id=session_id)
                    category = TestCategory.objects.get(id=category_id)
                    
                    questions_data = self._get_questions_from_db(category, question_count)
                    session.questions = questions_data
                    session.total_questions = len(questions_data)
                    session.status = 'in_progress'
                    session.save()
                except:
                    pass
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=generate)
        thread.daemon = True
        thread.start()
    
    def _detect_specialization(self, resume_text):
        """Определяем специализацию из текста резюме"""
        resume_text_lower = resume_text.lower()
        
        if any(tech in resume_text_lower for tech in ['react', 'angular', 'vue', 'frontend', 'javascript', 'typescript', 'css', 'html']):
            return 'Frontend Development'
        elif any(tech in resume_text_lower for tech in ['python', 'django', 'flask', 'java', 'spring', 'backend', 'node.js', 'express']):
            return 'Backend Development'
        elif any(tech in resume_text_lower for tech in ['fullstack', 'full stack', 'mern', 'mean']):
            return 'Fullstack Development'
        elif any(tech in resume_text_lower for tech in ['data', 'machine learning', 'ai', 'pandas', 'numpy', 'analytics']):
            return 'Data Science'
        elif any(tech in resume_text_lower for tech in ['devops', 'docker', 'kubernetes', 'aws', 'azure', 'ci/cd']):
            return 'DevOps'
        elif any(tech in resume_text_lower for tech in ['sql', 'database', 'postgresql', 'mysql', 'mongodb']):
            return 'Database'
        
        return 'General IT'
    
    def _map_specialization_to_category(self, specialization):
        """Маппинг специализации на название категории"""
        mapping = {
            'Frontend Development': 'Frontend Developer',
            'Backend Development': 'Backend Developer', 
            'Fullstack Development': 'Fullstack Developer',
            'Data Science': 'Data Scientist',
            'DevOps': 'DevOps Engineer',
            'Database': 'Database Administrator',
            'General IT': 'IT Specialist'
        }
        return mapping.get(specialization, 'IT Specialist')
    """Начать новый тест с AI-генерацией вопросов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        print(f"=== НАЧАЛО ТЕСТИРОВАНИЯ ===")
        print(f"Пользователь: {request.user.email}")
        print(f"Данные запроса: {request.data}")
        
        # Используем упрощенный сериализатор
        category_id = request.data.get('category_id')
        question_count = request.data.get('question_count', 10)
        
        try:
            # Проверяем активный тест
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
            from resumes.models import Resume
            resume = Resume.objects.filter(
                user=request.user
            ).order_by('-upload_date').first()
            
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
                    category = None
            
            # Если категория не указана, создаем/получаем категорию по умолчанию
            if not category:
                category, _ = TestCategory.objects.get_or_create(
                    name='Frontend Development',
                    defaults={'description': 'Тестирование для Frontend разработчиков (React, JavaScript, TypeScript, CSS)'}
                )
            
            questions_data = []
            
            # Генерация AI-вопросов на основе резюме
            print("Пытаемся сгенерировать AI-вопросы из резюме...")
            
            try:
                from core.services.gemini_service import GeminiService
                gemini = GeminiService()
                
                # Получаем текст резюме
                resume_text = resume.extracted_text or ""
                
                if resume_text and len(resume_text) > 50:
                    # Определяем специализацию из резюме
                    specialization = self._detect_specialization(resume_text)
                    print(f"Определенная специализация: {specialization}")
                    
                    # Определяем уровень опыта
                    experience = self._detect_experience(resume_text)
                    print(f"Определенный опыт: {experience} лет")
                    
                    # Генерируем вопросы через Gemini
                    ai_questions = gemini.generate_test_questions(
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
                                question_text=q_data['question_text'][:500],
                                question_type=q_data['question_type'],
                                options=q_data.get('options', []),
                                correct_answer=json.dumps(q_data['correct_answer']) if isinstance(q_data['correct_answer'], list) else str(q_data['correct_answer']),
                                explanation=q_data.get('explanation', '')[:500],
                                difficulty=q_data.get('difficulty', 3),
                                time_limit_seconds=90,
                                is_temporary=True
                            )
                            questions_data.append(question.id)
                            print(f"Создан вопрос: {question.id}")
                        except Exception as e:
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
                questions_data = self._get_questions_from_db(category, question_count)
            
            print(f"Всего вопросов подготовлено: {len(questions_data)}")
            
            if len(questions_data) < 5:  # Минимум 5 вопросов
                return Response({
                    'error': f'Недостаточно вопросов. Доступно: {len(questions_data)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Создаем сессию тестирования
            session = TestSession.objects.create(
                user=request.user,
                category=category,
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
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _detect_specialization(self, resume_text):
        """Определяем специализацию из текста резюме"""
        resume_text_lower = resume_text.lower()
        
        # Проверяем технологии
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
        
        return 'general'
    
    def _detect_experience(self, resume_text):
        """Определяем опыт из резюме"""
        import re
        
        # Ищем упоминания опыта
        experience_patterns = [
            r'(\d+)\s*год[а]?\s+опыт[а]?',
            r'опыт\s+работы\s+(\d+)',
            r'(\d+)\s*лет\s+в\s+разработке',
            r'(\d+)\s*год[а]?\s+в\s+it'
        ]
        
        for pattern in experience_patterns:
            match = re.search(pattern, resume_text.lower())
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        
        return 1  # По умолчанию 1 год
    
    def _map_experience_to_difficulty(self, experience_years):
        """Маппим опыт на уровень сложности"""
        if experience_years < 1:
            return 'easy'
        elif experience_years < 3:
            return 'medium'
        else:
            return 'hard'
    
    def _get_questions_from_db(self, category, question_count):
        """Получить вопросы из базы данных"""
        try:
            if category:
                questions = TestQuestion.objects.filter(
                    category=category,
                    is_active=True,
                    is_temporary=False
                )
            else:
                questions = TestQuestion.objects.filter(
                    is_active=True,
                    is_temporary=False
                )
            
            # Берем случайные вопросы
            questions = questions.order_by('?')[:question_count]
            return [q.id for q in questions]
            
        except Exception as e:
            print(f"Ошибка получения вопросов из базы: {e}")
            return []

class GetQuestionView(APIView):
    """Получить следующий вопрос теста"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, session_id):
        print(f"=== ЗАПРОС ВОПРОСА ===")
        print(f"Сессия: {session_id}, Пользователь: {request.user.email}")
        
        try:
            session = get_object_or_404(
                TestSession,
                id=session_id,
                user=request.user,
                status='in_progress'
            )
            
            print(f"Найдена сессия: {session.id}, вопросы: {session.questions}")
            print(f"Текущие ответы: {session.user_answers}")
            
            # Находим неотвеченные вопросы
            answered_questions = []
            if session.user_answers:
                answered_questions = [str(q_id) for q_id in session.user_answers.keys()]
            
            print(f"Отвеченные вопросы: {answered_questions}")
            
            # Получаем все вопросы сессии
            all_question_ids = [str(q_id) for q_id in session.questions]
            
            # Находим следующий неотвеченный вопрос
            remaining_questions = [q for q in all_question_ids if q not in answered_questions]
            
            print(f"Оставшиеся вопросы: {remaining_questions}")
            
            if not remaining_questions:
                print("Все вопросы отвечены, тест завершен")
                return Response({
                    'message': 'Все вопросы уже отвечены',
                    'completed': True,
                    'total_questions': session.total_questions,
                    'answered_questions': len(answered_questions)
                })
            
            # Берем первый неотвеченный вопрос
            question_id = int(remaining_questions[0])
            print(f"Следующий вопрос ID: {question_id}")
            
            question = get_object_or_404(TestQuestion, id=question_id)
            
            question_data = TestQuestionSerializer(question).data
            
            # Добавляем информацию о прогрессе
            current_question_num = len(answered_questions) + 1
            total_questions = session.total_questions
            
            print(f"Прогресс: {current_question_num}/{total_questions}")
            
            progress = {
                'current': current_question_num,
                'total': total_questions,
                'percentage': int((current_question_num / total_questions) * 100),
                'remaining': total_questions - current_question_num + 1,
                'answered': len(answered_questions)
            }
            
            response_data = {
                'question': question_data,
                'progress': progress,
                'session_id': session.id,
                'completed': False
            }
            
            print(f"Отправляем вопрос: {question_id}")
            
            return Response(response_data)
            
        except Exception as e:
            print(f"Ошибка в GetQuestionView: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    """Получить следующий вопрос теста"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, session_id):
        session = get_object_or_404(
            TestSession,
            id=session_id,
            user=request.user,
            status='in_progress'
        )
        
        # Находим неотвеченные вопросы
        answered_questions = list(session.user_answers.keys())
        remaining_questions = [q for q in session.questions if str(q) not in answered_questions]
        
        if not remaining_questions:
            return Response({
                'message': 'Все вопросы уже отвечены',
                'completed': True
            })
        
        # Берем первый неотвеченный вопрос
        question_id = remaining_questions[0]
        question = get_object_or_404(TestQuestion, id=question_id)
        
        question_data = TestQuestionSerializer(question).data
        
        # Добавляем прогресс
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
        print(f"=== ОТПРАВКА ОТВЕТА ===")
        print(f"Данные запроса: {request.data}")
        print(f"Тип answer в запросе: {type(request.data.get('answer'))}")
        print(f"Значение answer: {request.data.get('answer')}")
        
        try:
            # Принимаем любые данные и обрабатываем вручную
            session_id = request.data.get('session_id')
            question_id = request.data.get('question_id')
            answer = request.data.get('answer')
            
            # Проверяем обязательные поля
            if session_id is None or question_id is None or answer is None:
                return Response({
                    'error': 'Необходимы session_id, question_id и answer'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Преобразуем типы
            try:
                session_id = int(session_id)
                question_id = int(question_id)
            except (ValueError, TypeError):
                return Response({
                    'error': 'session_id и question_id должны быть числами'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Обрабатываем ответ
            processed_answer = self._process_answer(answer)
            print(f"Обработанный ответ: {processed_answer}, тип: {type(processed_answer)}")
            
            # Получаем сессию
            try:
                session = TestSession.objects.get(
                    id=session_id,
                    user=request.user,
                    status='in_progress'
                )
            except TestSession.DoesNotExist:
                return Response({
                    'error': 'Сессия тестирования не найдена или не активна'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем, что вопрос входит в тест
            if question_id not in session.questions:
                return Response(
                    {'error': 'Вопрос не входит в этот тест'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Получаем вопрос для проверки типа
            try:
                question = TestQuestion.objects.get(id=question_id)
                
                # Валидируем ответ в зависимости от типа вопроса
                validation_error = self._validate_answer(question, processed_answer)
                if validation_error:
                    return Response({
                        'error': validation_error
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except TestQuestion.DoesNotExist:
                return Response({
                    'error': 'Вопрос не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Сохраняем ответ
            user_answers = session.user_answers.copy() if session.user_answers else {}
            
            # Ключ всегда строка
            user_answers[str(question_id)] = processed_answer
            
            session.user_answers = user_answers
            
            # Обновляем время
            if session.started_at:
                elapsed = (timezone.now() - session.started_at).total_seconds()
                session.time_spent_seconds = int(elapsed)
            
            session.save()
            
            print(f"Ответ сохранен: вопрос {question_id} -> {processed_answer}")
            print(f"Текущие ответы: {session.user_answers}")
            
            return Response({
                'success': True,
                'session_id': session.id,
                'next_question_available': True,
                'current_answers_count': len(session.user_answers),
                'total_questions': session.total_questions
            })
            
        except Exception as e:
            print(f"Ошибка в SubmitAnswerView: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_answer(self, answer):
        """Обработка ответа в правильный формат"""
        if answer is None:
            return ""
        
        # Если это уже строка
        if isinstance(answer, str):
            return answer.strip()
        
        # Если это массив
        if isinstance(answer, list):
            try:
                return json.dumps(answer, ensure_ascii=False)
            except:
                return str(answer)
        
        # Если это число
        if isinstance(answer, (int, float)):
            return str(answer)
        
        # Если это булево значение
        if isinstance(answer, bool):
            return str(answer).lower()
        
        # Если это словарь
        if isinstance(answer, dict):
            try:
                return json.dumps(answer, ensure_ascii=False)
            except:
                return str(answer)
        
        # Для любых других типов
        return str(answer)
    
    def _validate_answer(self, question, answer):
        """Валидация ответа в зависимости от типа вопроса"""
        try:
            if question.question_type == 'single_choice':
                # Для single_choice ответ должен быть непустой строкой
                if not answer or not isinstance(answer, str) or answer.strip() == "":
                    return "Для вопроса с одиночным выбором необходим ответ"
            
            elif question.question_type == 'multiple_choice':
                # Для multiple_choice ответ должен быть валидным JSON массивом
                try:
                    parsed = json.loads(answer)
                    if not isinstance(parsed, list):
                        return "Для вопроса с множественным выбором ответ должен быть массивом"
                except json.JSONDecodeError:
                    return "Неверный формат ответа для множественного выбора"
            
            elif question.question_type == 'open_ended':
                # Для open_ended ответ должен быть строкой
                if not isinstance(answer, str):
                    return "Для открытого вопроса ответ должен быть строкой"
            
            return None
            
        except Exception as e:
            print(f"Ошибка валидации: {e}")
            return f"Ошибка валидации ответа: {str(e)}"
    """Отправить ответ на вопрос"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        print(f"=== ОТПРАВКА ОТВЕТА ===")
        print(f"Данные запроса: {request.data}")
        print(f"Тип answer: {type(request.data.get('answer'))}")
        
        try:
            # Используем сериализатор
            serializer = SubmitAnswerSerializer(data=request.data)
            if not serializer.is_valid():
                print(f"Ошибки валидации: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            session_id = data['session_id']
            question_id = data['question_id']
            answer = data['answer']
            
            # Получаем сессию
            try:
                session = TestSession.objects.get(
                    id=session_id,
                    user=request.user,
                    status='in_progress'
                )
            except TestSession.DoesNotExist:
                return Response({
                    'error': 'Сессия тестирования не найдена или не активна'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем, что вопрос входит в тест
            if int(question_id) not in session.questions:
                return Response(
                    {'error': 'Вопрос не входит в этот тест'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Получаем вопрос для проверки типа
            try:
                question = TestQuestion.objects.get(id=question_id)
                
                # Проверяем формат ответа в зависимости от типа вопроса
                if question.question_type == 'single_choice':
                    if not isinstance(answer, (str, int)):
                        return Response({
                            'error': 'Для single_choice ответ должен быть строкой или числом'
                        }, status=status.HTTP_400_BAD_REQUEST)
                elif question.question_type == 'multiple_choice':
                    if not isinstance(answer, list):
                        return Response({
                            'error': 'Для multiple_choice ответ должен быть массивом'
                        }, status=status.HTTP_400_BAD_REQUEST)
                elif question.question_type == 'open_ended':
                    if not isinstance(answer, str):
                        return Response({
                            'error': 'Для open_ended ответ должен быть строкой'
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
            except TestQuestion.DoesNotExist:
                return Response({
                    'error': 'Вопрос не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Сохраняем ответ
            user_answers = session.user_answers.copy() if session.user_answers else {}
            
            # Приводим answer_id к строке для JSON
            user_answers[str(question_id)] = answer
            
            session.user_answers = user_answers
            
            # Обновляем время
            if session.started_at:
                elapsed = (timezone.now() - session.started_at).total_seconds()
                session.time_spent_seconds = int(elapsed)
            
            session.save()
            
            print(f"Ответ сохранен: вопрос {question_id} -> {answer}")
            print(f"Текущие ответы: {session.user_answers}")
            
            return Response({
                'success': True,
                'session_id': session.id,
                'next_question_available': True,
                'current_answers_count': len(session.user_answers),
                'total_questions': session.total_questions
            })
            
        except Exception as e:
            print(f"Ошибка в SubmitAnswerView: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    """Отправить ответ на вопрос"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        print(f"=== ОТПРАВКА ОТВЕТА ===")
        print(f"Данные запроса: {request.data}")
        
        try:
            session_id = request.data.get('session_id')
            question_id = request.data.get('question_id')
            answer = request.data.get('answer')
            
            if not all([session_id, question_id, answer]):
                return Response({
                    'error': 'Необходимы session_id, question_id и answer'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            session = get_object_or_404(
                TestSession,
                id=session_id,
                user=request.user,
                status='in_progress'
            )
            
            # Проверяем, что вопрос входит в тест
            if int(question_id) not in session.questions:
                return Response(
                    {'error': 'Вопрос не входит в этот тест'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Сохраняем ответ
            user_answers = session.user_answers.copy() if session.user_answers else {}
            
            # Обрабатываем ответ в зависимости от типа
            if isinstance(answer, list):
                processed_answer = answer
            else:
                processed_answer = str(answer)
            
            user_answers[str(question_id)] = processed_answer
            session.user_answers = user_answers
            
            # Обновляем потраченное время
            if session.started_at:
                elapsed = (timezone.now() - session.started_at).total_seconds()
                session.time_spent_seconds = int(elapsed)
            
            session.save()
            
            print(f"Ответ сохранен: {question_id} -> {processed_answer}")
            
            return Response({
                'success': True,
                'session_id': session.id,
                'next_question_available': True
            })
            
        except Exception as e:
            print(f"Ошибка в SubmitAnswerView: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'Внутренняя ошибка сервера', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    """Отправить ответ на вопрос"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = SubmitAnswerSerializer(data=request.data)
        if serializer.is_valid():
            session = get_object_or_404(
                TestSession,
                id=serializer.validated_data['session_id'],
                user=request.user,
                status='in_progress'
            )
            
            question_id = str(serializer.validated_data['question_id'])
            
            # Проверяем, что вопрос входит в тест
            if int(question_id) not in session.questions:
                return Response(
                    {'error': 'Вопрос не входит в этот тест'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Сохраняем ответ
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
            
            session = get_object_or_404(
                TestSession,
                id=session_id,
                user=request.user
            )
            
            print(f"Сессия найдена: {session.id}, статус: {session.status}")
            
            if session.status == 'completed':
                return Response(
                    {'error': 'Тест уже завершен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Рассчитываем результаты
            print("Рассчитываем результаты...")
            score = session.calculate_score()
            
            session.status = 'completed'
            session.completed_at = timezone.now()
            
            # Обновляем время
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
                'passed': session.score >= session.passing_score if session.score else False,
                'message': 'Поздравляем! Вы успешно прошли тест.' if session.score >= session.passing_score else 'К сожалению, вы не прошли тест. Попробуйте снова через 7 дней.',
                'score': session.score,
                'correct_count': session.correct_count,
                'incorrect_count': session.incorrect_count,
                'total_questions': session.total_questions,
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
        return TestSession.objects.filter(
            user=self.request.user,
            status='completed'
        )


class TestHistoryView(generics.ListAPIView):
    """История тестирований пользователя"""
    serializer_class = TestSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TestSession.objects.filter(
            user=self.request.user,
            status='completed'
        ).order_by('-completed_at')
    
class SessionStatusView(APIView):
    """Проверить статус генерации вопросов"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, session_id):
        session = get_object_or_404(
            TestSession,
            id=session_id,
            user=request.user
        )
        
        return Response({
            'id': session.id,
            'status': session.status,
            'questions_ready': session.status == 'in_progress',
            'questions_count': len(session.questions) if session.questions else 0,
            'total_questions': session.total_questions,
            'is_ai_generated': session.is_ai_generated,
            'category': {
                'id': session.category.id if session.category else None,
                'name': session.category.name if session.category else None
            },
            'started_at': session.started_at
        })
    
class AvailableResumesView(APIView):
    """Получить список резюме пользователя для выбора"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from resumes.models import Resume
        
        resumes = Resume.objects.filter(
            user=request.user
        ).order_by('-upload_date')
        
        resumes_data = []
        for resume in resumes:
            resumes_data.append({
                'id': resume.id,
                'title': resume.original_filename,
                'upload_date': resume.upload_date,
                'status': resume.status,
                'overall_score': resume.overall_score,
                'analyzed_at': resume.analyzed_at,
                'preview': (resume.extracted_text or "")[:100] + "..." if resume.extracted_text else ""
            })
        
        return Response(resumes_data)
    
class PDFProxyView(APIView):
    """Proxy для PDF файлов чтобы обойти CORS"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        document = get_object_or_404(
            UserCertificate,
            id=document_id,
            user=request.user
        )
        
        if document.document_file:
            # Открываем файл локально
            with open(document.document_file.path, 'rb') as f:
                pdf_data = f.read()
            
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{document.title}.pdf"'
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        return Response(
            {'error': 'Файл не найден'},
            status=status.HTTP_404_NOT_FOUND
        )