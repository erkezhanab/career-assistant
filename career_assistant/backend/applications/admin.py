"""
Настройка админ-панели для откликов на вакансии.
"""

from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Отклики пользователей: кто, куда и с каким письмом откликнулся."""

    list_display = ('user', 'vacancy', 'status', 'letter_style', 'applied_at')
    # Фильтр по статусу: видно, сколько откликов получили приглашение
    list_filter = ('status', 'letter_style')
    # Поиск по связанным моделям: по email автора и названию вакансии
    search_fields = ('user__email', 'vacancy__name')
