"""
Маршруты приложения testing (префикс /api/testing/).

Сгруппированы по назначению: справочники, документы,
управление прохождением теста и результаты.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Категории тестов
    # GET — список направлений тестирования
    path('categories/', views.TestCategoryListView.as_view(), name='test_categories'),

    # Сертификаты и документы
    # GET — список документов, POST — загрузка нового
    path('documents/', views.UserCertificateListCreateView.as_view(), name='user_documents'),
    # GET/PUT/DELETE — работа с конкретным документом
    path('documents/<int:pk>/', views.UserCertificateDetailView.as_view(), name='document_detail'),

    # Статус тестирования
    # GET — можно ли начать тест, когда доступна пересдача, прошлый результат
    path('status/', views.TestStatusView.as_view(), name='test_status'),

    # Управление тестом
    # POST — начать тест (ИИ генерирует вопросы по резюме)
    path('start/', views.StartTestView.as_view(), name='start_test'),
    # GET — получить следующий неотвеченный вопрос
    path('session/<int:session_id>/question/', views.GetQuestionView.as_view(), name='get_question'),
    # POST — сохранить ответ на вопрос
    path('submit/', views.SubmitAnswerView.as_view(), name='submit_answer'),
    # POST — завершить тест и посчитать баллы
    path('complete/', views.CompleteTestView.as_view(), name='complete_test'),

    # Результаты
    # GET — подробные результаты одной попытки
    path('results/<int:pk>/', views.TestResultView.as_view(), name='test_result'),
    # GET — все пройденные тесты пользователя
    path('history/', views.TestHistoryView.as_view(), name='test_history'),
    # GET — проверка готовности вопросов (фронтенд опрашивает этот адрес,
    # пока ИИ генерирует вопросы в фоновом режиме)
    path('session/<int:session_id>/status/', views.SessionStatusView.as_view(), name='session_status'),

    # Получить резюме пользователя для выбора
    # GET — список резюме, на основе которых можно составить тест
    path('available-resumes/', views.AvailableResumesView.as_view(), name='available_resumes'),
]
