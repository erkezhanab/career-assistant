"""
Маршруты приложения resumes.

Подключаются в core/urls.py с префиксом /api/resumes/,
поэтому полный адрес = /api/resumes/ + путь, указанный здесь.
"""

from django.urls import path
from . import views

urlpatterns = [
    # POST — загрузка нового файла резюме
    path('upload/', views.ResumeUploadView.as_view(), name='resume_upload'),

    # GET — список всех резюме текущего пользователя.
    # Пустой путь '' = сам адрес /api/resumes/
    path('', views.UserResumesView.as_view(), name='user_resumes'),

    # <int:pk> — числовой параметр из адреса (id резюме),
    # он передаётся во view как аргумент pk
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='resume_detail'),

    # GET — результаты анализа конкретного резюме
    path('<int:pk>/analysis/', views.ResumeAnalysisView.as_view(), name='resume_analysis'),
]
