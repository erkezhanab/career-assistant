from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.GenerateInterviewView.as_view(), name='generate_interview'),
    path('', views.InterviewListView.as_view(), name='interview_list'),
    path('<int:pk>/', views.InterviewDetailView.as_view(), name='interview_detail'),
    path('<int:pk>/complete/', views.CompleteInterviewView.as_view(), name='complete_interview'),
    path('<int:pk>/feedback/', views.InterviewFeedbackView.as_view(), name='interview_feedback'),
]