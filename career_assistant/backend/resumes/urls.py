from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.ResumeUploadView.as_view(), name='resume_upload'),
    path('', views.UserResumesView.as_view(), name='user_resumes'),
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='resume_detail'),
    path('<int:pk>/analysis/', views.ResumeAnalysisView.as_view(), name='resume_analysis'),
]