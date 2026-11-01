"""
Фоновые задачи Celery.

Celery выполняет задачи по расписанию, вне обычного цикла
«запрос — ответ». Здесь описана регулярная очистка базы
от временных вопросов, созданных ИИ.

Примечание: в текущей версии проекта Celery не запущен (это пункт
плана развития в README). Ту же очистку можно выполнить вручную
командой: python manage.py cleanup_temp_questions
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from testing.models import TestQuestion


# @shared_task превращает обычную функцию в задачу Celery,
# которую можно поставить в очередь или в расписание
@shared_task
def cleanup_temporary_questions():
    """Задача для очистки временных вопросов"""
    # Зачем нужна: под каждый тест ИИ создаёт персональные вопросы
    # (is_temporary=True). Без очистки таблица росла бы бесконечно

    # Граница: всё, что старше 7 дней, считается ненужным.
    # Запас в неделю оставлен, чтобы не удалить вопросы
    # незавершённого теста
    cutoff_date = timezone.now() - timedelta(days=7)

    # created_at__lt — «создано раньше, чем» (less than)
    deleted_count, _ = TestQuestion.objects.filter(
        is_temporary=True,
        created_at__lt=cutoff_date
    ).delete()

    return deleted_count
