"""
Маршруты приложения vacancies (префикс /api/vacancies/).
"""

from django.urls import path
from . import views

urlpatterns = [
    # POST — поиск вакансий (HeadHunter или локальная база).
    # Именно POST, а не GET: параметров много, включая список языков,
    # и такие данные удобнее передавать в теле запроса
    path('search/', views.VacancySearchView.as_view(), name='vacancy_search'),

    # GET — все сохранённые вакансии (показываются при открытии страницы)
    path('', views.VacancyListView.as_view(), name='vacancy_list'),

    # GET — одна вакансия по id
    path('<int:pk>/', views.VacancyDetailView.as_view(), name='vacancy_detail'),
]
