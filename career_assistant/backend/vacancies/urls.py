from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.VacancySearchView.as_view(), name='vacancy_search'),
    path('', views.VacancyListView.as_view(), name='vacancy_list'),
    path('<int:pk>/', views.VacancyDetailView.as_view(), name='vacancy_detail'),
]