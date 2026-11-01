"""
Настройка встроенной админ-панели Django для пользователей.

Регистрация моделей здесь делает их доступными по адресу /admin —
это готовый интерфейс для просмотра и правки данных без написания кода.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, UserProfile


# Декоратор @admin.register подключает модель к админке
# и связывает её с классом настроек ниже
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Настройка отображения пользователей.

    Наследуется от DjangoUserAdmin, чтобы сохранить правильную работу
    с паролями (хеширование, форма смены пароля). Стандартный
    ModelAdmin сохранил бы пароль открытым текстом.
    """

    # Колонки в списке пользователей
    list_display = ('email', 'first_name', 'last_name', 'specialization', 'is_staff', 'is_active', 'date_joined')
    # Фильтры в боковой панели
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    # Поля, по которым работает строка поиска
    search_fields = ('email', 'first_name', 'last_name')
    # Сортировка: новые пользователи сверху
    ordering = ('-date_joined',)

    # Группировка полей на странице редактирования.
    # Переопределена, потому что у стандартного UserAdmin
    # первым полем идёт username, которого в нашей модели нет
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'phone', 'specialization')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )

    # Поля формы создания нового пользователя.
    # password1 и password2 — ввод пароля с подтверждением
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
    )

    # Дату регистрации менять нельзя — она проставляется автоматически
    readonly_fields = ('date_joined',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Настройки уведомлений пользователей."""

    list_display = ('user', 'search_frequency', 'notifications_enabled', 'email_notifications')
    list_filter = ('search_frequency', 'notifications_enabled')
    # Двойное подчёркивание — переход по связи: поиск по email владельца
    search_fields = ('user__email',)
