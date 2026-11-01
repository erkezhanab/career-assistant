"""
Маршруты приложения interviews (префикс /api/interviews/).

Порядок адресов отражает этапы работы с интервью:
создание -> прохождение -> завершение -> разбор.
"""

from django.urls import path
from . import views

urlpatterns = [
    # POST — создать интервью (ИИ генерирует вопросы)
    path('generate/', views.GenerateInterviewView.as_view(), name='generate_interview'),

    # GET — история пройденных собеседований
    path('', views.InterviewListView.as_view(), name='interview_list'),

    # GET/PATCH — одно интервью: получить вопросы или сохранить ответы
    path('<int:pk>/', views.InterviewDetailView.as_view(), name='interview_detail'),

    # POST — завершить интервью и отправить ответы на анализ ИИ
    path('<int:pk>/complete/', views.CompleteInterviewView.as_view(), name='complete_interview'),

    # GET — посмотреть разбор ранее пройденного интервью
    path('<int:pk>/feedback/', views.InterviewFeedbackView.as_view(), name='interview_feedback'),
]
