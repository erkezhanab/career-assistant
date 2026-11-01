"""
Сериализаторы для административной панели.

  - AdminUserSerializer       — полные данные пользователя + его статистика
  - AdminUserUpdateSerializer — ограниченный набор полей для правки админом
  - AdminStatsSerializer      — сводные показатели системы
"""

from rest_framework import serializers
from .models import User, UserProfile


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Пользователь глазами администратора.

    В отличие от обычного профиля, показывает служебные поля (права,
    даты входа) и количество созданных пользователем записей.
    """

    # Вычисляемые поля: значение возвращает метод get_<имя поля>
    profile = serializers.SerializerMethodField()
    resume_count = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone',
            'specialization', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'profile', 'resume_count',
            'application_count'
        )
        # Даты проставляет система, менять их вручную нельзя
        read_only_fields = ('date_joined', 'last_login')

    def get_profile(self, obj):
        """Настройки уведомлений пользователя (если профиль создан)."""
        try:
            profile = obj.profile
            return {
                'notifications_enabled': profile.notifications_enabled,
                'search_frequency': profile.search_frequency,
                'email_notifications': profile.email_notifications,
                'created_at': profile.created_at,
                'updated_at': profile.updated_at
            }
        except UserProfile.DoesNotExist:
            # У старых аккаунтов профиля может не быть — возвращаем None,
            # чтобы админка не падала с ошибкой
            return None

    def get_resume_count(self, obj):
        """Сколько резюме загрузил пользователь."""
        # obj.resumes — обратная связь от модели Resume.
        # Имя задано параметром related_name='resumes' в models.py
        return obj.resumes.count()

    def get_application_count(self, obj):
        """Сколько откликов отправил пользователь."""
        # related_name='applications' в модели Application
        return obj.applications.count()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Поля, которые администратор вправе изменить.

    Список намеренно короткий: email (он же логин), пароль и флаги
    is_staff / is_superuser сюда не входят, чтобы через этот запрос
    нельзя было выдать кому-то права администратора.
    """

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'specialization', 'is_active')


class AdminStatsSerializer(serializers.Serializer):
    """
    Сводные показатели для панели администратора.

    Обычный Serializer, а не ModelSerializer: данные собираются
    из нескольких моделей сразу и не соответствуют одной таблице.
    """

    total_users = serializers.IntegerField()         # всего пользователей
    active_users = serializers.IntegerField()        # не заблокированных
    new_users_today = serializers.IntegerField()     # зарегистрировались сегодня
    total_resumes = serializers.IntegerField()       # загружено резюме
    total_applications = serializers.IntegerField()  # отправлено откликов
    active_vacancies = serializers.IntegerField()    # вакансий в базе
