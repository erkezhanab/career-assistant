"""
Административные представления (views) — панель управления для администратора.

  - IsAdminUser                — правило доступа: только суперпользователь
  - AdminUserListView          — список пользователей с поиском и фильтром
  - AdminUserDetailView        — просмотр и правка данных пользователя
  - AdminToggleUserActiveView  — блокировка / разблокировка аккаунта
  - AdminStatsView             — сводная статистика системы

Все представления закрыты правилом IsAdminUser: обычный пользователь
получит ответ 403 (доступ запрещён).
"""

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import User
from .admin_serializers import (
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AdminStatsSerializer
)
from resumes.models import Resume
from applications.models import Application
from vacancies.models import Vacancy


class IsAdminUser(permissions.BasePermission):
    """
    Собственное правило доступа.

    DRF вызывает has_permission перед каждым запросом: если метод
    вернёт False, обработчик даже не запустится — ответ будет 403.
    """

    def has_permission(self, request, view):
        # Проверка request.user нужна на случай анонимного запроса,
        # когда пользователя в запросе вообще нет
        return request.user and request.user.is_superuser


class AdminUserListView(generics.ListAPIView):
    """
    Список всех пользователей с поиском и фильтрацией.
    GET /api/auth/admin/users/?search=...&is_active=true
    """

    # Два правила сразу: сначала проверка входа, затем прав администратора
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        """Формирует выборку с учётом параметров поиска из адреса запроса."""
        queryset = User.objects.all().order_by('-date_joined')

        # Фильтрация
        # query_params — параметры после «?» в адресе
        search = self.request.query_params.get('search', '')
        is_active = self.request.query_params.get('is_active', None)

        if search:
            # Q(...) | Q(...) означает «ИЛИ»: строка ищется сразу
            # по email, имени, фамилии и телефону
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )

        if is_active is not None:
            # Параметры адреса всегда строки, поэтому 'true'
            # преобразуется в настоящее True
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def get(self, request, *args, **kwargs):
        # Проверка прав
        # Дублирует IsAdminUser намеренно — «защита в глубину»:
        # если правило доступа случайно уберут, данные всё равно не утекут
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to access this resource'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().get(request, *args, **kwargs)


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и редактирование пользователя администратором.
    GET/PUT/PATCH /api/auth/admin/users/<id>/
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = User.objects.all()

    def get_serializer_class(self):
        """
        Разные сериализаторы для чтения и записи.

        При чтении отдаются все данные, при изменении разрешён
        лишь ограниченный набор полей — чтобы нельзя было
        случайно перезаписать пароль или дату регистрации.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserUpdateSerializer
        return AdminUserSerializer


class AdminToggleUserActiveView(APIView):
    """
    Блокировка и разблокировка аккаунта.
    POST /api/auth/admin/users/<id>/toggle-active/

    Переключатель: повторный вызов возвращает прежнее состояние.
    Аккаунты не удаляются, а деактивируются — так сохраняются
    связанные данные (резюме, отклики, результаты тестов).
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            # not меняет значение на противоположное
            user.is_active = not user.is_active
            user.save()

            return Response({
                'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
                'is_active': user.is_active
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminStatsView(APIView):
    """
    Сводная статистика системы для панели администратора.
    GET /api/auth/admin/stats/
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = timezone.now().date()

        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            # date_joined__date сравнивает только дату, без времени
            'new_users_today': User.objects.filter(date_joined__date=today).count(),
            'total_resumes': Resume.objects.count(),
            'total_applications': Application.objects.count(),
            # У модели Vacancy нет поля is_active: все сохранённые
            # вакансии считаются действующими
            'active_vacancies': Vacancy.objects.count(),
        }

        # Сериализатор приводит значения к нужным типам
        # и отдаёт только описанные в нём поля
        serializer = AdminStatsSerializer(stats)
        return Response(serializer.data)
