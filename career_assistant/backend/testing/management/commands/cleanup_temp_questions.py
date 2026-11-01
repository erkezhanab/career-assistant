"""
Команда очистки временных вопросов.

Запуск: python manage.py cleanup_temp_questions

Удаляет вопросы, которые ИИ сгенерировал под конкретные резюме
(is_temporary=True) и которые старше 7 дней. Без этой очистки
таблица вопросов постоянно росла бы.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from testing.models import TestQuestion


class Command(BaseCommand):
    """Своя команда Django. Текст help виден при вызове manage.py help."""

    help = 'Очистка временных вопросов старше 7 дней'

    def handle(self, *args, **options):
        """Метод, который выполняется при запуске команды."""
        # Всё, что создано раньше этой даты, подлежит удалению
        cutoff_date = timezone.now() - timedelta(days=7)

        # .delete() возвращает кортеж: общее число удалённых записей
        # и разбивку по моделям. Вторая часть не нужна — отсюда «_»
        deleted_count, _ = TestQuestion.objects.filter(
            is_temporary=True,
            created_at__lt=cutoff_date
        ).delete()

        # self.style.SUCCESS выводит сообщение зелёным цветом в консоли
        self.stdout.write(
            self.style.SUCCESS(f'Удалено временных вопросов: {deleted_count}')
        )
