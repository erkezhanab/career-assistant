"""
Настройка админ-панели для резюме.

Позволяет администратору просматривать загруженные резюме
и результаты их анализа ИИ.
"""

from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    """Отображение резюме в админке."""

    list_display = ('user', 'original_filename', 'status', 'overall_score', 'upload_date')
    # Фильтр по статусу удобен, чтобы быстро найти резюме
    # с ошибкой анализа (status='failed')
    list_filter = ('status', 'upload_date')
    search_fields = ('user__email', 'original_filename')

    # Поля только для чтения: их заполняет система и ИИ,
    # ручная правка привела бы к несогласованным данным
    readonly_fields = ('upload_date', 'analyzed_at', 'extracted_text', 'analysis_result')
