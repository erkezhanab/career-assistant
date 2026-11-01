"""
Модели приложения testing — проверка профессиональных знаний.

Ответственность модуля:
  - TestCategory    — направление тестирования (Программирование, Дизайн, ...)
  - TestQuestion    — один вопрос теста (из базы или сгенерированный ИИ)
  - TestSession     — прохождение теста пользователем + подсчёт результата
  - UserCertificate — дипломы/сертификаты/курсы, которые загрузил пользователь
"""

from django.db import models
from users.models import User
from django.utils import timezone
import json


class TestCategory(models.Model):
    """Категория (направление) тестов: Программирование, Data Science, Дизайн и т.д."""

    # unique=True — две категории с одинаковым названием создать нельзя
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TestQuestion(models.Model):
    """
    Вопрос теста.

    Вопросы бывают двух видов:
      - постоянные (is_temporary=False) — общий банк вопросов в базе;
      - временные (is_temporary=True)   — сгенерированы ИИ под конкретное резюме,
        потом удаляются командой cleanup_temp_questions.
    """

    # Тип вопроса определяет, как фронтенд рисует варианты ответа
    # и как потом проверяется правильность (см. TestSession._check_answer)
    QUESTION_TYPES = [
        ('multiple_choice', 'Множественный выбор'),  # несколько правильных ответов
        ('single_choice', 'Одиночный выбор'),        # один правильный ответ
        ('open_ended', 'Открытый вопрос'),           # ответ вводится текстом
    ]

    DIFFICULTY_LEVELS = [
        (1, 'Очень легко'),
        (2, 'Легко'),
        (3, 'Средне'),
        (4, 'Сложно'),
        (5, 'Очень сложно'),
    ]

    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()

    # Объяснение показывается после теста — чтобы пользователь понял свою ошибку
    explanation = models.TextField(blank=True)

    # Варианты ответа: ["вариант1", "вариант2", ...].
    # У открытых вопросов список пустой
    options = models.JSONField(default=list, blank=True)

    # Правильный ответ. Для multiple_choice хранится JSON-строкой: '["Java", "C++"]'
    correct_answer = models.TextField()

    difficulty = models.IntegerField(choices=DIFFICULTY_LEVELS, default=3)
    time_limit_seconds = models.IntegerField(default=90)  # таймер на один вопрос

    is_active = models.BooleanField(default=True)    # False = вопрос скрыт из выдачи
    is_temporary = models.BooleanField(default=False, verbose_name='Временный вопрос')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'difficulty', 'id']

    def __str__(self):
        return f"{self.category.name}: {self.question_text[:50]}..."


class UserCertificate(models.Model):
    """
    Документ пользователя: диплом, сертификат или пройденный курс.

    Подтверждает квалификацию и показывается в профиле.
    """

    DOCUMENT_TYPES = [
        ('diploma', 'Диплом'),
        ('certificate', 'Сертификат'),
        ('course', 'Курс'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')

    title = models.CharField(max_length=255, verbose_name='Название')
    issuer = models.CharField(max_length=255, verbose_name='Организация')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES,
                                     default='certificate', verbose_name='Тип документа')

    issue_date = models.DateField(verbose_name='Дата выдачи')
    # Срок действия есть не у всех документов (у диплома его нет) — поэтому null=True
    expiry_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')

    description = models.TextField(blank=True, verbose_name='Описание')

    # Скан документа. Необязателен: можно указать документ без файла
    document_file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name='Файл документа'
    )

    # Заполняются автоматически в save() — нужны для отображения
    # размера файла и выбора способа просмотра (PDF или картинка)
    file_size = models.IntegerField(null=True, blank=True, verbose_name='Размер файла')
    file_type = models.CharField(max_length=50, blank=True, verbose_name='Тип файла')

    is_verified = models.BooleanField(default=False, verbose_name='Проверен')  # проверка админом
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.get_document_type_display()})"

    def save(self, *args, **kwargs):
        """Перед сохранением сам вычисляет размер и расширение файла."""
        if self.document_file:
            self.file_size = self.document_file.size
            # Берём то, что после последней точки: "diploma.PDF" -> "pdf"
            self.file_type = self.document_file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)


class TestSession(models.Model):
    """
    Сессия тестирования — одна попытка прохождения теста.

    Хранит список выданных вопросов, ответы пользователя и итоговый результат.
    Здесь же находится вся логика проверки ответов и подсчёта баллов.
    """

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),       # создана, но не начата
        ('in_progress', 'В процессе'),# пользователь отвечает на вопросы
        ('completed', 'Завершено'),   # тест сдан, баллы посчитаны
        ('expired', 'Просрочено'),    # вышло время
        ('cancelled', 'Отменено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_sessions')

    # SET_NULL (а не CASCADE): если категорию удалят, историю
    # пройденных тестов терять нельзя — просто обнулится ссылка
    category = models.ForeignKey(TestCategory, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    total_questions = models.IntegerField(default=15)

    # Список id вопросов этой сессии: [12, 15, 23, ...].
    # Сохраняется, чтобы у каждого пользователя был свой набор вопросов
    questions = models.JSONField(default=list)

    # Ответы в формате {"id_вопроса": "ответ"}.
    # Ключ — строка, потому что в JSON ключи всегда строки
    user_answers = models.JSONField(default=dict)

    score = models.FloatField(null=True, blank=True)     # итоговый процент
    passing_score = models.FloatField(default=70.0)      # проходной балл

    is_ai_generated = models.BooleanField(default=False, verbose_name='Вопросы сгенерированы ИИ')

    time_limit_minutes = models.IntegerField(default=30)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)

    correct_count = models.IntegerField(default=0)
    incorrect_count = models.IntegerField(default=0)

    # Подробный разбор каждого вопроса для страницы результатов
    detailed_results = models.JSONField(default=list, blank=True)

    can_retake = models.BooleanField(default=True)                      # можно ли пересдать
    next_retake_date = models.DateTimeField(null=True, blank=True)      # когда откроется пересдача

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.status} - {self.score or 0}%"

    def calculate_score(self):
        """
        Главный метод подсчёта результата теста.

        Что делает:
          1. Проходит по всем ответам пользователя
          2. Сравнивает каждый с правильным ответом из базы
          3. Считает процент правильных и формирует подробный разбор
          4. Определяет, нужна ли пересдача (через 7 дней, если балл ниже проходного)

        Вызывается из CompleteTestView при завершении теста.
        """
        print(f"=== РАСЧЕТ РЕЗУЛЬТАТОВ ===")
        print(f"User answers: {self.user_answers}")

        # Пользователь не ответил ни на один вопрос — считать нечего
        if not self.user_answers:
            print("Нет ответов пользователя")
            return 0

        correct = 0
        detailed = []

        # Идём по всем ответам: ключ — id вопроса (строкой), значение — ответ
        for question_id_str, user_answer in self.user_answers.items():
            try:
                question_id = int(question_id_str)
                question = TestQuestion.objects.get(id=question_id)

                print(f"Проверка вопроса {question_id}: {question.question_text[:50]}...")
                print(f"Ответ пользователя: {user_answer}, тип: {type(user_answer)}")
                print(f"Правильный ответ в БД: {question.correct_answer}, тип: {type(question.correct_answer)}")

                # Сама проверка вынесена в отдельный метод,
                # так как для разных типов вопросов она разная
                is_correct = self._check_answer(question, user_answer)

                if is_correct:
                    correct += 1
                    print(f"✓ Правильно")
                else:
                    print(f"✗ Неправильно")

                # Собираем разбор: что спросили, что ответил, как правильно и почему
                detailed.append({
                    'question_id': question_id,
                    'question': question.question_text,
                    'user_answer': user_answer,
                    # Если правильный ответ был сохранён как JSON-массив — разворачиваем
                    # его обратно в список, чтобы фронтенд показал нормально
                    'correct_answer': json.loads(question.correct_answer) if isinstance(question.correct_answer, str) and question.correct_answer.startswith('[') else question.correct_answer,
                    'explanation': question.explanation,
                    'is_correct': is_correct,
                    'question_type': question.question_type,
                    'difficulty': question.difficulty
                })

            except TestQuestion.DoesNotExist:
                # Вопрос мог быть удалён (например, временный вопрос ИИ) —
                # пропускаем его, но не роняем подсчёт всего теста
                print(f"Вопрос {question_id} не найден")
                continue
            except Exception as e:
                print(f"Ошибка при проверке вопроса {question_id}: {e}")
                continue

        print(f"Правильных ответов: {correct} из {self.total_questions}")

        self.correct_count = correct
        self.incorrect_count = len(self.user_answers) - correct

        # Процент считается от ОБЩЕГО числа вопросов, а не от числа ответов:
        # пропущенные вопросы засчитываются как ошибка
        if self.total_questions > 0:
            self.score = (correct / self.total_questions) * 100
        else:
            self.score = 0

        self.detailed_results = detailed

        # Пересдача нужна только тем, кто не набрал проходной балл
        self.can_retake = self.score < self.passing_score

        if not self.can_retake:
            # Тест сдан — пересдавать не нужно
            self.next_retake_date = None
        else:
            # Не сдал — следующая попытка через неделю
            self.next_retake_date = timezone.now() + timezone.timedelta(days=7)

        print(f"Итоговый балл: {self.score}%")
        print(f"Можно пересдать: {self.can_retake}")

        return self.score

    def _check_answer(self, question, user_answer):
        """
        Проверка одного ответа. Логика зависит от типа вопроса.

        Возвращает True/False. Вспомогательный метод (нижнее подчёркивание
        в начале имени = используется только внутри этого класса).
        """
        try:
            # Правильный ответ в базе хранится строкой. Если это был список
            # (multiple_choice), он сохранён как JSON — пробуем развернуть
            if isinstance(question.correct_answer, str):
                try:
                    correct_answer = json.loads(question.correct_answer)
                except:
                    # Не JSON — значит обычная строка, оставляем как есть
                    correct_answer = question.correct_answer
            else:
                correct_answer = question.correct_answer

            print(f"Обработанный правильный ответ: {correct_answer}, тип: {type(correct_answer)}")

            if question.question_type == 'single_choice':
                # Один вариант: сравниваем строки без учёта регистра и пробелов
                return str(user_answer).strip().lower() == str(correct_answer).strip().lower()

            elif question.question_type == 'multiple_choice':
                # Несколько вариантов: приводим оба ответа к спискам
                if not isinstance(user_answer, list):
                    user_answer = [user_answer] if user_answer else []

                if not isinstance(correct_answer, list):
                    correct_answer = [correct_answer] if correct_answer else []

                # Сортируем перед сравнением, чтобы порядок выбора вариантов
                # пользователем не влиял на результат: [A, B] == [B, A]
                user_sorted = sorted([str(item).strip().lower() for item in user_answer])
                correct_sorted = sorted([str(item).strip().lower() for item in correct_answer])

                return user_sorted == correct_sorted

            elif question.question_type == 'open_ended':
                # Открытый вопрос: простое текстовое сравнение
                return str(user_answer).strip().lower() == str(correct_answer).strip().lower()

            return False

        except Exception as e:
            # Любая ошибка проверки = ответ не засчитан, но тест не ломается
            print(f"Ошибка при проверке ответа: {e}")
            return False

    def can_start_test(self):
        """
        Можно ли сейчас начать/перепройти тест.

        Защищает от повторного прохождения: сдавшим — нельзя,
        несдавшим — только после даты пересдачи.
        """
        if self.status == 'completed':
            if not self.can_retake:
                return False

            # Неделя с прошлой попытки ещё не прошла
            if self.next_retake_date and timezone.now() < self.next_retake_date:
                return False

        return self.status in ['pending', 'expired', 'cancelled']

    def get_remaining_time(self):
        """Сколько секунд осталось до конца теста (для таймера на фронтенде)."""
        if self.status != 'in_progress' or not self.started_at:
            return 0

        elapsed = (timezone.now() - self.started_at).total_seconds()
        remaining = (self.time_limit_minutes * 60) - elapsed - self.time_spent_seconds

        # max(0, ...) — таймер не уходит в минус
        return max(0, remaining)
