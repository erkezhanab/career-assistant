"""
Команда создания стандартных категорий тестов.

Запуск: python manage.py create_test_categories

Заполняет справочник направлений тестирования. Команду можно
запускать повторно — дубликаты не создаются.
"""

from django.core.management.base import BaseCommand
from testing.models import TestCategory


class Command(BaseCommand):
    help = 'Создание стандартных категорий тестов'

    def handle(self, *args, **options):
        # Список направлений, доступных пользователю при выборе теста
        categories = [
            {'name': 'Программирование', 'description': 'Тесты по программированию и разработке ПО'},
            {'name': 'Data Science', 'description': 'Тесты по анализу данных и машинному обучению'},
            {'name': 'Дизайн', 'description': 'Тесты по дизайну и UX/UI'},
            {'name': 'Маркетинг', 'description': 'Тесты по маркетингу и продвижению'},
            {'name': 'Менеджмент', 'description': 'Тесты по управлению и менеджменту'},
            {'name': 'Аналитика', 'description': 'Тесты по аналитике и бизнес-анализу'},
            {'name': 'Тестирование', 'description': 'Тесты по QA и тестированию ПО'},
            {'name': 'DevOps', 'description': 'Тесты по DevOps и инфраструктуре'},
            {'name': 'Общие', 'description': 'Общие профессиональные вопросы'},
        ]

        for cat_data in categories:
            # get_or_create ищет запись по name; если её нет — создаёт.
            # Именно это делает команду безопасной для повторного запуска
            category, created = TestCategory.objects.get_or_create(
                name=cat_data['name'],
                # defaults применяются только при создании новой записи
                defaults={'description': cat_data['description']}
            )

            # created показывает, была запись создана или уже существовала
            if created:
                self.stdout.write(f'Создана категория: {cat_data["name"]}')
            else:
                self.stdout.write(f'Категория уже существует: {cat_data["name"]}')
