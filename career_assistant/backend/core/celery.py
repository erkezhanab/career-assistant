from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from testing.models import TestQuestion

@shared_task
def cleanup_temporary_questions():
    """Задача для очистки временных вопросов"""
    cutoff_date = timezone.now() - timedelta(days=7)
    deleted_count, _ = TestQuestion.objects.filter(
        is_temporary=True,
        created_at__lt=cutoff_date
    ).delete()
    return deleted_count