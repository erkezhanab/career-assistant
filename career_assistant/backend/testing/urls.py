from django.urls import path
from . import views

urlpatterns = [
    # Категории тестов
    path('categories/', views.TestCategoryListView.as_view(), name='test_categories'),
    
    # Сертификаты и документы
    path('documents/', views.UserCertificateListCreateView.as_view(), name='user_documents'),
    path('documents/<int:pk>/', views.UserCertificateDetailView.as_view(), name='document_detail'),
    
    # Статус тестирования
    path('status/', views.TestStatusView.as_view(), name='test_status'),
    
    # Управление тестом
    path('start/', views.StartTestView.as_view(), name='start_test'),
    path('session/<int:session_id>/question/', views.GetQuestionView.as_view(), name='get_question'),
    path('submit/', views.SubmitAnswerView.as_view(), name='submit_answer'),
    path('complete/', views.CompleteTestView.as_view(), name='complete_test'),
    
    # Результаты
    path('results/<int:pk>/', views.TestResultView.as_view(), name='test_result'),
    path('history/', views.TestHistoryView.as_view(), name='test_history'),
        path('session/<int:session_id>/status/', views.SessionStatusView.as_view(), name='session_status'),
    
    # Получить резюме пользователя для выбора
    path('available-resumes/', views.AvailableResumesView.as_view(), name='available_resumes'),
]