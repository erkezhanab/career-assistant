"""
Маршруты приложения users (префикс /api/auth/).

Отвечают за регистрацию, вход, профиль и административные функции.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import admin_views

urlpatterns = [
    # Существующие эндпоинты
    # POST — регистрация нового аккаунта
    path('register/', views.RegisterView.as_view(), name='register'),

    # POST — вход, выдаёт пару токенов (access и refresh)
    path('login/', views.LoginView.as_view(), name='login'),

    # POST — обновление access-токена по refresh-токену.
    # Готовый view из библиотеки simplejwt, свой писать не нужно.
    # Благодаря ему пользователь не вводит пароль повторно каждый день
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # GET/PUT — настройки профиля
    path('profile/', views.UserProfileView.as_view(), name='profile'),

    # PUT — смена пароля
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # GET — данные текущего пользователя (нужны интерфейсу после входа)
    path('user-info/', views.UserInfoView.as_view(), name='user_info'),

    # Админские эндпоинты
    # Доступны только администраторам — проверка прав находится
    # внутри самих представлений в admin_views.py
    path('admin/users/', admin_views.AdminUserListView.as_view(), name='admin_users'),
    path('admin/users/<int:pk>/', admin_views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    # Блокировка / разблокировка аккаунта
    path('admin/users/<int:pk>/toggle-active/', admin_views.AdminToggleUserActiveView.as_view(), name='admin_toggle_user_active'),
    # Общая статистика системы для панели администратора
    path('admin/stats/', admin_views.AdminStatsView.as_view(), name='admin_stats'),
]
