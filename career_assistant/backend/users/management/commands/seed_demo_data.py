"""
Команда заполнения базы демонстрационными данными.

Запуск: python manage.py seed_demo_data

Создаёт полный набор связанных данных для показа работы системы:
пользователей, категории и вопросы тестов, вакансии по городам
Казахстана, резюме, отклики, пройденное интервью и сертификат.

Команда идемпотентна — её можно запускать повторно, дубликаты
не создаются (везде используется get_or_create).
"""

import random
from datetime import date, timedelta
# quote_plus кодирует текст для подстановки в адрес ссылки
# ("Frontend разработчик" -> "Frontend+%D1%80%D0%B0...")
from urllib.parse import quote_plus

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from applications.models import Application
from interviews.models import Interview
from resumes.models import Resume
from testing.models import TestCategory, TestQuestion, TestSession, UserCertificate
from users.models import User, UserProfile
from vacancies.models import Vacancy


class Command(BaseCommand):
    help = 'Заполняет базу демонстрационными данными для локальной разработки'

    def handle(self, *args, **options):
        """
        Главный метод команды.

        Порядок вызовов важен: сначала создаются независимые сущности
        (пользователи, категории, вакансии), затем зависящие от них
        (резюме -> отклики -> интервью), иначе не на что будет ссылаться.
        """
        self.stdout.write('Создание тестовых данных...')

        admin = self._create_user(
            'admin@example.com', 'admin12345', 'Админ', 'Админов',
            is_staff=True, is_superuser=True, specialization='Администратор системы',
        )
        demo = self._create_user(
            'demo@example.com', 'demo12345', 'Иван', 'Иванов',
            specialization='Python Developer',
        )
        demo2 = self._create_user(
            'anna@example.com', 'demo12345', 'Анна', 'Смирнова',
            specialization='UX/UI Designer',
        )

        categories = self._create_categories()
        self._create_questions(categories['Программирование'])

        vacancies = self._create_vacancies()
        resume = self._create_resume(demo)
        self._create_resume(demo2)

        self._create_applications(demo, resume, vacancies)
        self._create_interview(demo, resume)
        self._create_certificate(demo)
        self._create_test_session(demo, categories['Программирование'])

        self.stdout.write(self.style.SUCCESS('Готово! Тестовые данные созданы.'))
        self.stdout.write('')
        self.stdout.write('Логины для входа (email / пароль):')
        self.stdout.write('  admin@example.com / admin12345  (суперпользователь)')
        self.stdout.write('  demo@example.com  / demo12345')
        self.stdout.write('  anna@example.com  / demo12345')

    def _create_user(self, email, password, first_name, last_name, **extra):
        """Создаёт пользователя с профилем, если его ещё нет."""
        # get_or_create ищет по email; created покажет, создана ли запись
        user, created = User.objects.get_or_create(
            email=email,
            # ** распаковывает дополнительные параметры (is_staff и т.п.)
            defaults={'first_name': first_name, 'last_name': last_name, **extra},
        )
        if created:
            # set_password хеширует пароль — иначе войти будет невозможно
            user.set_password(password)
            user.save()
            UserProfile.objects.get_or_create(user=user)
            self.stdout.write(f'  + Пользователь: {email}')
        else:
            # Пароль существующему пользователю не меняем,
            # чтобы не сбросить тот, который он задал сам
            self.stdout.write(f'  = Пользователь уже существует: {email}')
        return user

    def _create_categories(self):
        """Создаёт категории тестов и возвращает их словарём по названию."""
        categories = {
            'Программирование': 'Тесты по программированию и разработке ПО',
            'Data Science': 'Тесты по анализу данных и машинному обучению',
            'Дизайн': 'Тесты по дизайну и UX/UI',
            'Менеджмент': 'Тесты по управлению и менеджменту',
        }
        result = {}
        for name, description in categories.items():
            category, created = TestCategory.objects.get_or_create(
                name=name, defaults={'description': description},
            )
            result[name] = category
            if created:
                self.stdout.write(f'  + Категория: {name}')
        return result

    def _create_questions(self, category):
        """Добавляет примеры вопросов всех трёх типов в указанную категорию."""
        questions = [
            {
                'question_type': 'single_choice',
                'question_text': 'Какой оператор используется для проверки идентичности объектов в Python?',
                'options': ['==', 'is', 'equals', '==='],
                'correct_answer': 'is',
                'explanation': '"is" сравнивает идентичность объектов, "==" сравнивает значения.',
                'difficulty': 2,
            },
            {
                'question_type': 'single_choice',
                'question_text': 'Какая структура данных в Python является неизменяемой?',
                'options': ['list', 'dict', 'tuple', 'set'],
                'correct_answer': 'tuple',
                'explanation': 'tuple — неизменяемая последовательность.',
                'difficulty': 1,
            },
            {
                'question_type': 'multiple_choice',
                'question_text': 'Какие из перечисленных фреймворков относятся к Python?',
                'options': ['Django', 'React', 'Flask', 'Spring'],
                'correct_answer': ['Django', 'Flask'],
                'explanation': 'Django и Flask — веб-фреймворки на Python.',
                'difficulty': 2,
            },
            {
                'question_type': 'open_ended',
                'question_text': 'Как называется принцип ООП, позволяющий скрывать детали реализации?',
                'options': [],
                'correct_answer': 'инкапсуляция',
                'explanation': 'Инкапсуляция скрывает внутреннее устройство объекта.',
                'difficulty': 3,
            },
        ]
        created_count = 0
        for q in questions:
            _, created = TestQuestion.objects.get_or_create(
                category=category,
                question_text=q['question_text'],
                defaults={
                    'question_type': q['question_type'],
                    'options': q['options'],
                    'correct_answer': q['correct_answer'] if isinstance(q['correct_answer'], str) else str(q['correct_answer']),
                    'explanation': q['explanation'],
                    'difficulty': q['difficulty'],
                },
            )
            if created:
                created_count += 1
        if created_count:
            self.stdout.write(f'  + Вопросов добавлено: {created_count}')

    # (должность, компания, город, зарплата от, зарплата до, навыки, опыт, график)
    VACANCIES = [
        ('Frontend разработчик (React)', 'Kolesa Group', 'Алматы', 700000, 1200000,
         ['JavaScript', 'React', 'TypeScript', 'Redux'], 'От 1 года до 3 лет', 'Гибрид'),
        ('Senior Frontend разработчик', 'Kaspi.kz', 'Алматы', 1500000, 2500000,
         ['JavaScript', 'React', 'TypeScript', 'Next.js'], 'От 3 до 6 лет', 'Офис'),
        ('Frontend разработчик (Vue.js)', 'Chocofamily', 'Алматы', 600000, 1000000,
         ['JavaScript', 'Vue.js', 'CSS'], 'От 1 года до 3 лет', 'Гибрид'),
        ('Junior Frontend разработчик', 'Digital Nomads', 'Астана', 300000, 500000,
         ['HTML', 'CSS', 'JavaScript', 'React'], 'Нет опыта', 'Офис'),
        ('Frontend разработчик', 'Freedom Holding', 'Астана', 800000, 1400000,
         ['JavaScript', 'React', 'TypeScript'], 'От 1 года до 3 лет', 'Офис'),
        ('Frontend разработчик', 'IT Solutions KZ', 'Шымкент', 450000, 750000,
         ['JavaScript', 'React', 'HTML', 'CSS'], 'От 1 года до 3 лет', 'Офис'),

        ('Python разработчик (Django)', 'Kaspi.kz', 'Алматы', 900000, 1600000,
         ['Python', 'Django', 'PostgreSQL', 'REST API'], 'От 1 года до 3 лет', 'Офис'),
        ('Backend разработчик Python', 'Technodom', 'Алматы', 800000, 1300000,
         ['Python', 'FastAPI', 'PostgreSQL', 'Docker'], 'От 1 года до 3 лет', 'Гибрид'),
        ('Senior Python разработчик', 'Halyk Bank', 'Астана', 1600000, 2600000,
         ['Python', 'Django', 'Kubernetes', 'PostgreSQL'], 'От 3 до 6 лет', 'Офис'),
        ('Java разработчик', 'Halyk Bank', 'Алматы', 1000000, 1800000,
         ['Java', 'Spring', 'PostgreSQL', 'Kafka'], 'От 1 года до 3 лет', 'Офис'),
        ('Backend разработчик (Node.js)', 'Beeline Kazakhstan', 'Астана', 850000, 1400000,
         ['JavaScript', 'Node.js', 'MongoDB', 'Express'], 'От 1 года до 3 лет', 'Гибрид'),
        ('Fullstack разработчик', 'Smart Systems', 'Караганда', 500000, 900000,
         ['JavaScript', 'React', 'Python', 'Django'], 'От 1 года до 3 лет', 'Удаленная работа'),
        ('PHP разработчик (Laravel)', 'WebCraft', 'Актобе', 400000, 700000,
         ['PHP', 'Laravel', 'MySQL'], 'От 1 года до 3 лет', 'Офис'),
        ('Go разработчик', 'Kolesa Group', 'Алматы', 1200000, 2000000,
         ['Go', 'PostgreSQL', 'Kubernetes', 'gRPC'], 'От 3 до 6 лет', 'Гибрид'),

        ('Мобильный разработчик (Flutter)', 'Chocofamily', 'Алматы', 700000, 1200000,
         ['Flutter', 'Dart', 'REST API'], 'От 1 года до 3 лет', 'Гибрид'),
        ('iOS разработчик (Swift)', 'Kaspi.kz', 'Алматы', 1100000, 1900000,
         ['Swift', 'iOS', 'UIKit'], 'От 1 года до 3 лет', 'Офис'),
        ('Android разработчик (Kotlin)', 'Freedom Holding', 'Астана', 1000000, 1700000,
         ['Kotlin', 'Android', 'Jetpack Compose'], 'От 1 года до 3 лет', 'Офис'),

        ('Data Analyst', 'Kaspi.kz', 'Алматы', 600000, 1100000,
         ['SQL', 'Python', 'Power BI', 'Excel'], 'От 1 года до 3 лет', 'Офис'),
        ('Аналитик данных', 'Air Astana', 'Астана', 550000, 950000,
         ['SQL', 'Python', 'Tableau'], 'Нет опыта', 'Офис'),
        ('Data Scientist', 'Kolesa Group', 'Алматы', 1200000, 2100000,
         ['Python', 'Machine Learning', 'SQL', 'Pandas'], 'От 3 до 6 лет', 'Гибрид'),
        ('ML Engineer', 'Tengri Lab', 'Алматы', 1300000, 2200000,
         ['Python', 'PyTorch', 'Machine Learning', 'Docker'], 'От 3 до 6 лет', 'Удаленная работа'),
        ('Бизнес-аналитик', 'KazMunayGas', 'Атырау', 600000, 1000000,
         ['SQL', 'BPMN', 'Excel'], 'От 1 года до 3 лет', 'Офис'),

        ('QA Engineer (ручное тестирование)', 'Technodom', 'Алматы', 400000, 700000,
         ['Testing', 'Postman', 'SQL'], 'Нет опыта', 'Офис'),
        ('QA Automation Engineer', 'Beeline Kazakhstan', 'Алматы', 800000, 1400000,
         ['Python', 'Selenium', 'Pytest', 'CI/CD'], 'От 1 года до 3 лет', 'Гибрид'),
        ('Тестировщик ПО', 'IT Solutions KZ', 'Павлодар', 350000, 600000,
         ['Testing', 'Postman'], 'Нет опыта', 'Офис'),

        ('DevOps Engineer', 'Kaspi.kz', 'Алматы', 1300000, 2300000,
         ['Docker', 'Kubernetes', 'CI/CD', 'Linux'], 'От 3 до 6 лет', 'Офис'),
        ('DevOps инженер', 'Halyk Bank', 'Астана', 1100000, 1900000,
         ['Docker', 'Kubernetes', 'Ansible', 'Linux'], 'От 1 года до 3 лет', 'Офис'),
        ('Системный администратор', 'Казахтелеком', 'Усть-Каменогорск', 350000, 600000,
         ['Linux', 'Windows Server', 'Networking'], 'От 1 года до 3 лет', 'Офис'),

        ('UX/UI дизайнер', 'Chocofamily', 'Алматы', 600000, 1100000,
         ['Figma', 'UX Research', 'Prototyping'], 'От 1 года до 3 лет', 'Гибрид'),
        ('Product Designer', 'Kolesa Group', 'Алматы', 900000, 1600000,
         ['Figma', 'UX Research', 'Design System'], 'От 3 до 6 лет', 'Гибрид'),
        ('Графический дизайнер', 'Media Group', 'Астана', 350000, 600000,
         ['Photoshop', 'Illustrator', 'Figma'], 'Нет опыта', 'Офис'),

        ('Product Manager', 'Kaspi.kz', 'Алматы', 1200000, 2200000,
         ['Product Management', 'Analytics', 'Agile'], 'От 3 до 6 лет', 'Офис'),
        ('Project Manager', 'Freedom Holding', 'Астана', 800000, 1400000,
         ['Agile', 'Scrum', 'Jira'], 'От 1 года до 3 лет', 'Офис'),
        ('Руководитель IT-отдела', 'Казахтелеком', 'Караганда', 900000, 1500000,
         ['Management', 'ITIL', 'Agile'], 'Более 6 лет', 'Офис'),

        ('1С программист', 'Астана Групп', 'Астана', 500000, 900000,
         ['1С', 'SQL'], 'От 1 года до 3 лет', 'Офис'),
        ('Техническая поддержка', 'Beeline Kazakhstan', 'Тараз', 250000, 400000,
         ['Support', 'Windows'], 'Нет опыта', 'Офис'),
        ('Маркетолог (digital)', 'Chocofamily', 'Алматы', 450000, 800000,
         ['Google Analytics', 'SMM', 'SEO'], 'От 1 года до 3 лет', 'Гибрид'),
        ('HR-менеджер (IT-рекрутинг)', 'Tengri Lab', 'Алматы', 500000, 850000,
         ['Recruiting', 'HR'], 'От 1 года до 3 лет', 'Удаленная работа'),
    ]

    def _create_vacancies(self):
        vacancies = []
        created_count = 0

        for index, item in enumerate(self.VACANCIES, start=1):
            name, company, city, salary_from, salary_to, skills, experience, schedule = item
            hh_id = 2000000 + index

            vacancy, created = Vacancy.objects.get_or_create(
                hh_id=hh_id,
                defaults={
                    'name': name,
                    'company': company,
                    'city': city,
                    'salary_from': salary_from,
                    'salary_to': salary_to,
                    'salary_currency': 'KZT',
                    'description': (
                        f'Компания {company} ищет специалиста на позицию «{name}» в городе {city}. '
                        f'Вам предстоит работать над развитием продукта в команде профессионалов. '
                        f'Мы предлагаем официальное трудоустройство, медицинскую страховку, '
                        f'обучение за счёт компании и гибкий график ({schedule.lower()}).'
                    ),
                    'requirements': (
                        f'Требуемые навыки: {", ".join(skills)}. Опыт работы: {experience.lower()}. '
                        f'Будет плюсом: английский язык, опыт работы в команде по Agile.'
                    ),
                    'experience': experience,
                    'employment_type': 'Полная занятость',
                    'schedule': schedule,
                    'skills': skills,
                    # Ссылка на реальный поиск по этой должности на hh.kz
                    'url': f'https://hh.kz/search/vacancy?text={quote_plus(name)}',
                    'published_at': timezone.now() - timedelta(days=random.randint(0, 14)),
                },
            )
            vacancies.append(vacancy)
            if created:
                created_count += 1

        if created_count:
            self.stdout.write(f'  + Вакансий добавлено: {created_count}')

        return vacancies

    def _create_resume(self, user):
        """
        Создаёт демо-резюме с готовыми результатами анализа.

        Оценки и рекомендации записываются сразу, вручную: это
        демонстрационные данные, ИИ для них не вызывается.
        """
        # Если резюме уже есть, повторно не создаём
        existing = Resume.objects.filter(user=user).first()
        if existing:
            return existing
        # ContentFile создаёт файл «на лету», из строки в памяти,
        # без чтения настоящего файла с диска
        content = ContentFile(
            f'Демо-резюме пользователя {user.email}'.encode('utf-8'),
            name=f'resume_{user.id}.txt',
        )
        resume = Resume.objects.create(
            user=user,
            file=content,
            original_filename=f'resume_{user.email}.txt',
            status='approved',
            overall_score=82.5,
            strong_points='Сильные навыки работы с Python и Django, опыт командной разработки.',
            improvements='Стоит добавить больше количественных результатов в описание опыта.',
            recommendations='Добавьте раздел с проектами и ссылками на GitHub.',
            analyzed_at=timezone.now(),
            extracted_text='Опыт работы: 3 года. Навыки: Python, Django, PostgreSQL.',
            skills=['Python', 'Django', 'PostgreSQL', 'REST API', 'Git'],
            experience_years=3,
            education=[{'degree': 'Бакалавр', 'field': 'Информационные технологии', 'institution': 'КазНУ'}],
        )
        self.stdout.write(f'  + Резюме: {resume.original_filename}')
        return resume

    def _create_applications(self, user, resume, vacancies):
        """Создаёт отклики на первые три вакансии с разными статусами."""
        styles = ['formal', 'friendly', 'brief', 'creative']
        # Разные статусы нужны, чтобы на демонстрации было видно
        # все варианты отображения в списке откликов
        statuses = ['pending', 'viewed', 'invited']
        created_count = 0
        # enumerate даёт и номер, и сам элемент — номер используется
        # для выбора стиля письма и статуса по очереди
        for i, vacancy in enumerate(vacancies[:3]):
            _, created = Application.objects.get_or_create(
                user=user, vacancy=vacancy,
                defaults={
                    'resume': resume,
                    'cover_letter': f'Здравствуйте! Хочу откликнуться на вакансию "{vacancy.name}" в компании {vacancy.company}.',
                    'letter_style': styles[i % len(styles)],
                    'status': statuses[i % len(statuses)],
                },
            )
            if created:
                created_count += 1
        if created_count:
            self.stdout.write(f'  + Откликов добавлено: {created_count}')

    def _create_interview(self, user, resume):
        """Создаёт одно завершённое интервью с ответами и разбором."""
        # exists() быстрее count() или .first(): базе достаточно
        # найти одну запись и сразу остановиться
        if Interview.objects.filter(user=user).exists():
            return
        questions = [
            'Расскажите о своем опыте работы с Django.',
            'Как вы оптимизируете запросы к базе данных?',
            'Опишите ситуацию, когда вам пришлось быстро решать сложную проблему.',
        ]
        Interview.objects.create(
            user=user,
            resume=resume,
            interview_type='technical',
            questions=questions,
            answers=['У меня 3 года опыта с Django...', 'Использую select_related и индексы...', ''],
            feedback={'overall_score': 75, 'comment': 'Хорошие ответы, но нужно больше примеров.'},
            preparation_tips='Повторите основы ORM и работу с индексами в PostgreSQL.',
            completed=True,
            completed_at=timezone.now(),
        )
        self.stdout.write('  + Интервью создано')

    def _create_certificate(self, user):
        """Добавляет один документ (пройденный курс) в профиль."""
        if UserCertificate.objects.filter(user=user).exists():
            return
        UserCertificate.objects.create(
            user=user,
            title='Python для разработчиков',
            issuer='Stepik',
            document_type='course',
            issue_date=date.today() - timedelta(days=200),
            description='Курс по основам backend-разработки на Python.',
            is_verified=True,
        )
        self.stdout.write('  + Сертификат создан')

    def _create_test_session(self, user, category):
        """Создаёт завершённую попытку теста для истории тестирований."""
        if TestSession.objects.filter(user=user, category=category).exists():
            return
        # values_list('id', flat=True) достаёт из базы только столбец id
        # и возвращает простой список чисел, а не объекты целиком
        questions = list(TestQuestion.objects.filter(category=category).values_list('id', flat=True))
        TestSession.objects.create(
            user=user,
            category=category,
            status='completed',
            total_questions=len(questions),
            questions=questions,
            user_answers={},
            score=75.0,
            correct_count=3,
            incorrect_count=1,
            started_at=timezone.now() - timedelta(minutes=20),
            completed_at=timezone.now(),
        )
        self.stdout.write('  + Сессия тестирования создана')
