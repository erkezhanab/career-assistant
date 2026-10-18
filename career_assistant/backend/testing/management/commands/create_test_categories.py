from django.core.management.base import BaseCommand
from testing.models import TestCategory


class Command(BaseCommand):
    help = 'Создание стандартных категорий тестов'
    
    def handle(self, *args, **options):
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
            category, created = TestCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            
            if created:
                self.stdout.write(f'Создана категория: {cat_data["name"]}')
            else:
                self.stdout.write(f'Категория уже существует: {cat_data["name"]}')