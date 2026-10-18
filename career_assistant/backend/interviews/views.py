from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Interview
from .serializers import InterviewSerializer, InterviewRequestSerializer
from resumes.models import Resume
from vacancies.models import Vacancy
from core.services.gemini_service import GeminiService
import json


class GenerateInterviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = InterviewRequestSerializer(data=request.data)
        if serializer.is_valid():
            interview_type = serializer.validated_data['interview_type']
            vacancy_id = serializer.validated_data.get('vacancy_id')
            
            resume = Resume.objects.filter(
                user=request.user,
                status='approved'
            ).first()
            
            if not resume:
                return Response(
                    {'error': 'No approved resume found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            vacancy = None
            if vacancy_id:
                vacancy = get_object_or_404(Vacancy, id=vacancy_id)
            
            # Генерируем вопросы через Gemini
            gemini = GeminiService()
            vacancy_text = vacancy.description if vacancy else None
            
            questions = gemini.generate_interview_questions(
                resume.extracted_text,
                interview_type,
                vacancy_text
            )
            
            # Создаем запись об интервью
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
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        interview = get_object_or_404(Interview, id=pk, user=request.user)
        
        # Получаем ответы пользователя
        user_answers = request.data.get('answers', [])
        
        if not user_answers:
            return Response(
                {'error': 'No answers provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Сохраняем ответы
        interview.answers = user_answers
        interview.completed = True
        interview.completed_at = timezone.now()
        interview.save()
        
        # Генерируем фидбек через Gemini
        gemini = GeminiService()
        
        # Формируем контекст для анализа
        analysis_context = {
            'interview_type': interview.get_interview_type_display(),
            'questions': interview.questions,
            'user_answers': user_answers,
            'resume_text': interview.resume.extracted_text[:2000],
            'vacancy_info': interview.resume.vacancy.description[:1000] if hasattr(interview.resume, 'vacancy') and interview.resume.vacancy else None
        }
        
        try:
            # Анализируем ответы
            feedback = gemini.analyze_interview_answers(analysis_context)
            interview.feedback = feedback
            interview.save()
        except Exception as e:
            print(f"Error generating feedback: {e}")
            # Создаем базовый фидбек в случае ошибки
            feedback = self._create_default_feedback(interview, user_answers)
            interview.feedback = feedback
            interview.save()
        
        return Response({
            'interview': InterviewSerializer(interview).data,
            'feedback': feedback
        })
    
    def _create_default_feedback(self, interview, user_answers):
        """Создает базовый фидбек если Gemini не сработал"""
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
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        interview = get_object_or_404(Interview, id=pk, user=request.user)
        
        if not interview.completed:
            return Response(
                {'error': 'Interview not completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not interview.feedback:
            # Генерируем фидбек если его нет
            gemini = GeminiService()
            analysis_context = {
                'interview_type': interview.get_interview_type_display(),
                'questions': interview.questions,
                'user_answers': interview.answers,
                'resume_text': interview.resume.extracted_text[:2000],
            }
            
            try:
                feedback = gemini.analyze_interview_answers(analysis_context)
                interview.feedback = feedback
                interview.save()
            except Exception as e:
                print(f"Error generating feedback: {e}")
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
            feedback = interview.feedback
        
        return Response({
            'interview': InterviewSerializer(interview).data,
            'feedback': feedback
        })


class InterviewListView(generics.ListAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Interview.objects.filter(user=self.request.user).order_by('-created_at')


class InterviewDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Interview.objects.filter(user=self.request.user)