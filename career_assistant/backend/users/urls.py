from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import admin_views

urlpatterns = [
    # Существующие эндпоинты
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('user-info/', views.UserInfoView.as_view(), name='user_info'),
    
    # Админские эндпоинты
    path('admin/users/', admin_views.AdminUserListView.as_view(), name='admin_users'),
    path('admin/users/<int:pk>/', admin_views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:pk>/toggle-active/', admin_views.AdminToggleUserActiveView.as_view(), name='admin_toggle_user_active'),
    path('admin/stats/', admin_views.AdminStatsView.as_view(), name='admin_stats'),
]