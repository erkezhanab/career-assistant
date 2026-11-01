"""
Настройка админ-панели для вакансий и истории поисковых запросов.
"""

from django.contrib import admin
from .models import Vacancy, SearchQuery


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    """Вакансии: загруженные с HeadHunter и добавленные вручную."""

    list_display = ('name', 'company', 'city', 'salary_from', 'salary_to', 'published_at')
    list_filter = ('city', 'employment_type')
    search_fields = ('name', 'company', 'city')


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """
    История поисковых запросов.

    Полезна для аналитики: показывает, какие должности
    и города ищут пользователи чаще всего.
    """

    list_display = ('user', 'position', 'city', 'salary_desired', 'created_at')
    list_filter = ('city',)
    search_fields = ('user__email', 'position')
