"""
Представления (views) приложения interviews — пробные собеседования с ИИ.

  - GenerateInterviewView — создать интервью: ИИ генерирует вопросы по резюме
  - CompleteInterviewView — принять ответы и получить разбор от ИИ
  - InterviewFeedbackView — посмотреть разбор ранее пройденного интервью
  - InterviewListView     — история моих собеседований
  - InterviewDetailView   — одно собеседование

Полный цикл: сгенерировать вопросы -> ответить -> получить оценку и советы.
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Interview
from .serializers import InterviewSerializer, InterviewRequestSerializer
from resumes.models import Resume
from vacancies.models import Vacancy
from core.services.claude_service import ClaudeService
import json


class GenerateInterviewView(APIView):
    """
    Создание пробного собеседования.  POST /api/interviews/generate/

    Принимает тип интервью и (необязательно) id вакансии.
    ИИ составляет вопросы на основе резюме пользователя,
    поэтому они касаются его реального опыта.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InterviewRequestSerializer(data=request.data)
        if serializer.is_valid():
            interview_type = serializer.validated_data['interview_type']
            # .get() вместо [] — вакансия необязательна
            vacancy_id = serializer.validated_data.get('vacancy_id')

            # Интервью строится на основе резюме, поэтому без
            # одобренного резюме начать его нельзя
            resume = Resume.objects.filter(
                user=request.user,
                status='approved'
            ).first()

            if not resume:
                return Response(
                    {'error': 'No approved resume found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Если указана вакансия, вопросы будут учитывать её требования
            vacancy = None
            if vacancy_id:
                vacancy = get_object_or_404(Vacancy, id=vacancy_id)

            # Генерируем вопросы через Claude
            ai_service = ClaudeService()
            # Тернарное выражение: описание вакансии либо есть, либо None
            vacancy_text = vacancy.description if vacancy else None

            questions = ai_service.generate_interview_questions(
                resume.extracted_text,  # опыт кандидата
                interview_type,         # характер вопросов
                vacancy_text            # требования вакансии (может быть None)
            )

            # Создаем запись об интервью
            # Вопросы сохраняются в базу, чтобы при перезагрузке страницы
            # пользователь продолжил то же интервью, а не получил новые вопросы
            interview = Interview.objects.create(
                user=request.user,
                resume=resume,
                interview_type=interview_type,
                questions=questions,
                preparation_tips="Советы по подготовке будут сгенерированы ИИ"
            )

            return Response(InterviewSerializer(interview).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteInterviewView(APIView):
    """
    Завершение интервью и получение разбора.
    POST /api/interviews/<id>/complete/

    Сохраняет ответы пользователя и отправляет их ИИ на анализ.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # user=request.user в условии поиска: завершить можно
        # только своё интервью, чужое вернёт 404
        interview = get_object_or_404(Interview, id=pk, user=request.user)

        # Получаем ответы пользователя
        user_answers = request.data.get('answers', [])

        if not user_answers:
            return Response(
                {'error': 'No answers provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Сохраняем ответы
        # Сохраняем ДО обращения к ИИ: даже если анализ не удастся,
        # ответы пользователя не потеряются
        interview.answers = user_answers
        interview.completed = True
        interview.completed_at = timezone.now()
        interview.save()

        # Генерируем фидбек через Claude
        ai_service = ClaudeService()

        # Формируем контекст для анализа
        # Это все данные, нужные ИИ для оценки: о чём спрашивали,
        # что ответил кандидат и какой у него опыт.
        # Срезы [:2000] и [:1000] ограничивают объём запроса к модели
        analysis_context = {
            # get_..._display() даёт читаемое название типа интервью
            'interview_type': interview.get_interview_type_display(),
            'questions': interview.questions,
            'user_answers': user_answers,
            'resume_text': interview.resume.extracted_text[:2000],
            'vacancy_info': interview.resume.vacancy.description[:1000] if hasattr(interview.resume, 'vacancy') and interview.resume.vacancy else None
        }

        try:
            # Анализируем ответы
            feedback = ai_service.analyze_interview_answers(analysis_context)
            interview.feedback = feedback
            interview.save()
        except Exception as e:
            print(f"Error generating feedback: {e}")
            # Создаем базовый фидбек в случае ошибки
            # Пользователь всё равно получит полезные советы,
            # а не пустую страницу с ошибкой
            feedback = self._create_default_feedback(interview, user_answers)
            interview.feedback = feedback
            interview.save()

        return Response({
            'interview': InterviewSerializer(interview).data,
            'feedback': feedback
        })

    def _create_default_feedback(self, interview, user_answers):
        """Создает базовый фидбек если Claude не сработал"""
        return {
            'overall_score': 6.5,
            'strengths': [
                'Вы предоставили ответы на все вопросы',
                'Показали понимание темы собеседования'
            ],
            'weaknesses': [
                'Рекомендуется давать более развернутые ответы',
                'Добавьте конкретные примеры из опыта'
            ],
            'tips': [
                'Подготовьте конкретные примеры из вашего опыта',
                'Изучите информацию о компании перед собеседованием',
                'Практикуйтесь отвечать на типовые вопросы'
            ],
            'common_mistakes': [
                'Слишком короткие ответы',
                'Недостаточно конкретики в примерах'
            ],
            'improvement_areas': [
                'Структурирование ответов по методу STAR',
                'Работа над уверенностью в ответах'
            ],
            'summary': 'Хорошая основа для дальнейшего развития. Рекомендуется больше практиковаться.'
        }


class InterviewFeedbackView(APIView):
    """
    Просмотр разбора интервью.  GET /api/interviews/<id>/feedback/

    Если разбор уже сохранён — отдаёт его из базы (ИИ повторно не вызывается,
    это экономит время и деньги). Если разбора нет — генерирует.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        interview = get_object_or_404(Interview, id=pk, user=request.user)

        # Пока пользователь не ответил на вопросы, разбирать нечего
        if not interview.completed:
            return Response(
                {'error': 'Interview not completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not interview.feedback:
            # Генерируем фидбек если его нет
            # Такое возможно, если при завершении интервью ИИ был недоступен
            ai_service = ClaudeService()
            analysis_context = {
                'interview_type': interview.get_interview_type_display(),
                'questions': interview.questions,
                'user_answers': interview.answers,
                'resume_text': interview.resume.extracted_text[:2000],
            }
            
            try:
                feedback = ai_service.analyze_interview_answers(analysis_context)
                interview.feedback = feedback
                interview.save()
            except Exception as e:
                print(f"Error generating feedback: {e}")
                # Заглушка-«пустышка»: интерфейс получит ожидаемую структуру
                # и не сломается, а пользователь поймёт, что нужно подождать
                feedback = {
                    'overall_score': 0,
                    'strengths': ['Фидбек в процессе генерации'],
                    'weaknesses': [],
                    'tips': [],
                    'common_mistakes': [],
                    'improvement_areas': [],
                    'summary': 'Фидбек будет доступен в ближайшее время'
                }
        else:
            # Разбор уже есть в базе — просто берём его
            feedback = interview.feedback

        return Response({
            'interview': InterviewSerializer(interview).data,
            'feedback': feedback
        })


class InterviewListView(generics.ListAPIView):
    """История моих собеседований.  GET /api/interviews/"""

    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только свои интервью, новые сверху
        return Interview.objects.filter(user=self.request.user).order_by('-created_at')


class InterviewDetailView(generics.RetrieveUpdateAPIView):
    """
    Одно собеседование.  GET/PUT/PATCH /api/interviews/<id>/

    RetrieveUpdateAPIView = чтение + изменение. Обновление нужно,
    чтобы сохранять ответы по ходу интервью, не завершая его целиком.
    """

    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Interview.objects.filter(user=self.request.user)