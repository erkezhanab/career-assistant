"""
Маршруты приложения applications (префикс /api/applications/).
"""

from django.urls import path
from . import views

urlpatterns = [
    # POST — отправить отклик на вакансию
    path('apply/', views.ApplyView.as_view(), name='apply'),

    # POST — сгенерировать сопроводительное письмо через ИИ.
    # Отдельный адрес, так как письмо сначала показывается
    # пользователю для правки и только потом отправляется
    path('generate-letter/', views.GenerateCoverLetterView.as_view(), name='generate_letter'),

    # GET — список моих откликов
    path('', views.ApplicationListView.as_view(), name='application_list'),

    # GET — один отклик по id
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
]
