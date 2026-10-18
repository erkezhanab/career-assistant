from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from testing.models import TestQuestion


class Command(BaseCommand):
    help = 'Очистка временных вопросов старше 7 дней'
    
    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count, _ = TestQuestion.objects.filter(
            is_temporary=True,
            created_at__lt=cutoff_date
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Удалено временных вопросов: {deleted_count}')
        )