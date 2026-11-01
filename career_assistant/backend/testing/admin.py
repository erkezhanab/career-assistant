"""
Настройка админ-панели для тестирования: категории, вопросы,
документы пользователей и сессии прохождения тестов.
"""

from django.contrib import admin
from .models import TestCategory, TestQuestion, UserCertificate, TestSession


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    """Направления тестирования."""

    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    """Банк вопросов: постоянные и созданные ИИ."""

    list_display = ('category', 'question_type', 'question_text_short', 'difficulty', 'is_active')
    list_filter = ('category', 'question_type', 'difficulty', 'is_active')
    search_fields = ('question_text', 'explanation')

    def question_text_short(self, obj):
        """
        Укороченный текст вопроса для таблицы.

        Свой метод нужен потому, что полный текст вопроса
        растянул бы колонку на весь экран.
        """
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text

    # Заголовок колонки для метода выше
    question_text_short.short_description = 'Вопрос'


@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    """
    Документы пользователей.

    Через фильтр is_verified администратор находит документы,
    ожидающие проверки.
    """

    list_display = ('user', 'title', 'issuer', 'issue_date', 'is_verified')
    list_filter = ('is_verified', 'issue_date')
    search_fields = ('user__email', 'title', 'issuer')


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    """Попытки прохождения тестов и их результаты."""

    list_display = ('user', 'category', 'status', 'score', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('user__email',)
