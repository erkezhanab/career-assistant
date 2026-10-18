from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.ApplyView.as_view(), name='apply'),
    path('generate-letter/', views.GenerateCoverLetterView.as_view(), name='generate_letter'),
    path('', views.ApplicationListView.as_view(), name='application_list'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
]