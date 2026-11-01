"""
Настройка админ-панели для пробных собеседований.
"""

from django.contrib import admin
from .models import Interview


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    """Пробные интервью: тип, статус прохождения и даты."""

    list_display = ('user', 'interview_type', 'completed', 'created_at', 'completed_at')
    # По фильтру completed видно, сколько интервью доводят до конца
    list_filter = ('interview_type', 'completed')
    search_fields = ('user__email',)
