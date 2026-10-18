from django.db import models
from users.models import User
from django.utils import timezone
import json


class TestCategory(models.Model):
    """Категории тестов"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class TestQuestion(models.Model):
    """Вопросы для тестирования"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Множественный выбор'),
        ('single_choice', 'Одиночный выбор'),
        ('open_ended', 'Открытый вопрос'),
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
    explanation = models.TextField(blank=True)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField()
    difficulty = models.IntegerField(choices=DIFFICULTY_LEVELS, default=3)
    time_limit_seconds = models.IntegerField(default=90)
    is_active = models.BooleanField(default=True)
    is_temporary = models.BooleanField(default=False, verbose_name='Временный вопрос')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'difficulty', 'id']
    
    def __str__(self):
        return f"{self.category.name}: {self.question_text[:50]}..."


class UserCertificate(models.Model):
    """Документы пользователя (дипломы, сертификаты, курсы)"""
    DOCUMENT_TYPES = [
        ('diploma', 'Диплом'),
        ('certificate', 'Сертификат'),
        ('course', 'Курс'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255, verbose_name='Название')
    issuer = models.CharField(max_length=255, verbose_name='Организация')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='certificate', verbose_name='Тип документа')
    issue_date = models.DateField(verbose_name='Дата выдачи')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')
    description = models.TextField(blank=True, verbose_name='Описание')
    document_file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name='Файл документа'
    )
    file_size = models.IntegerField(null=True, blank=True, verbose_name='Размер файла')
    file_type = models.CharField(max_length=50, blank=True, verbose_name='Тип файла')
    is_verified = models.BooleanField(default=False, verbose_name='Проверен')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-issue_date']
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
    
    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.get_document_type_display()})"
    
    def save(self, *args, **kwargs):
        # Автоматически определяем размер и тип файла
        if self.document_file:
            self.file_size = self.document_file.size
            self.file_type = self.document_file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)


class TestSession(models.Model):
    """Сессия тестирования"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершено'),
        ('expired', 'Просрочено'),
        ('cancelled', 'Отменено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_sessions')
    category = models.ForeignKey(TestCategory, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_questions = models.IntegerField(default=15)
    questions = models.JSONField(default=list)
    user_answers = models.JSONField(default=dict)
    score = models.FloatField(null=True, blank=True)
    passing_score = models.FloatField(default=70.0)
    is_ai_generated = models.BooleanField(default=False, verbose_name='Вопросы сгенерированы ИИ')
    time_limit_minutes = models.IntegerField(default=30)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    incorrect_count = models.IntegerField(default=0)
    detailed_results = models.JSONField(default=list, blank=True)
    can_retake = models.BooleanField(default=True)
    next_retake_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.status} - {self.score or 0}%"
    
    def calculate_score(self):
        """Расчет результатов теста с улучшенной обработкой JSON"""
        print(f"=== РАСЧЕТ РЕЗУЛЬТАТОВ ===")
        print(f"User answers: {self.user_answers}")
        
        if not self.user_answers:
            print("Нет ответов пользователя")
            return 0
        
        correct = 0
        detailed = []
        
        for question_id_str, user_answer in self.user_answers.items():
            try:
                question_id = int(question_id_str)
                question = TestQuestion.objects.get(id=question_id)
                
                print(f"Проверка вопроса {question_id}: {question.question_text[:50]}...")
                print(f"Ответ пользователя: {user_answer}, тип: {type(user_answer)}")
                print(f"Правильный ответ в БД: {question.correct_answer}, тип: {type(question.correct_answer)}")
                
                # Проверяем ответ
                is_correct = self._check_answer(question, user_answer)
                
                if is_correct:
                    correct += 1
                    print(f"✓ Правильно")
                else:
                    print(f"✗ Неправильно")
                
                # Сохраняем детали
                detailed.append({
                    'question_id': question_id,
                    'question': question.question_text,
                    'user_answer': user_answer,
                    'correct_answer': json.loads(question.correct_answer) if isinstance(question.correct_answer, str) and question.correct_answer.startswith('[') else question.correct_answer,
                    'explanation': question.explanation,
                    'is_correct': is_correct,
                    'question_type': question.question_type,
                    'difficulty': question.difficulty
                })
                
            except TestQuestion.DoesNotExist:
                print(f"Вопрос {question_id} не найден")
                continue
            except Exception as e:
                print(f"Ошибка при проверке вопроса {question_id}: {e}")
                continue
        
        print(f"Правильных ответов: {correct} из {self.total_questions}")
        
        self.correct_count = correct
        self.incorrect_count = len(self.user_answers) - correct
        
        if self.total_questions > 0:
            self.score = (correct / self.total_questions) * 100
        else:
            self.score = 0
        
        self.detailed_results = detailed
        
        # Проверяем возможность пересдачи
        self.can_retake = self.score < self.passing_score
        
        if not self.can_retake:
            self.next_retake_date = None
        else:
            self.next_retake_date = timezone.now() + timezone.timedelta(days=7)
        
        print(f"Итоговый балл: {self.score}%")
        print(f"Можно пересдать: {self.can_retake}")
        
        return self.score
    
    def _check_answer(self, question, user_answer):
        """Проверка ответа с улучшенной обработкой"""
        try:
            # Обрабатываем правильный ответ из БД
            if isinstance(question.correct_answer, str):
                try:
                    # Пробуем распарсить JSON
                    correct_answer = json.loads(question.correct_answer)
                except:
                    # Если не JSON, оставляем как строку
                    correct_answer = question.correct_answer
            else:
                correct_answer = question.correct_answer
            
            print(f"Обработанный правильный ответ: {correct_answer}, тип: {type(correct_answer)}")
            
            # Проверяем в зависимости от типа вопроса
            if question.question_type == 'single_choice':
                # Для single_choice сравниваем как строки
                return str(user_answer).strip().lower() == str(correct_answer).strip().lower()
            
            elif question.question_type == 'multiple_choice':
                # Для multiple_choice проверяем что оба массива содержат одинаковые элементы
                if not isinstance(user_answer, list):
                    user_answer = [user_answer] if user_answer else []
                
                if not isinstance(correct_answer, list):
                    correct_answer = [correct_answer] if correct_answer else []
                
                # Сортируем и сравниваем
                user_sorted = sorted([str(item).strip().lower() for item in user_answer])
                correct_sorted = sorted([str(item).strip().lower() for item in correct_answer])
                
                return user_sorted == correct_sorted
            
            elif question.question_type == 'open_ended':
                # Для open_ended сравниваем как строки (можно добавить более сложную логику)
                return str(user_answer).strip().lower() == str(correct_answer).strip().lower()
            
            return False
            
        except Exception as e:
            print(f"Ошибка при проверке ответа: {e}")
            return False
    
    def can_start_test(self):
        """Может ли пользователь начать тест"""
        if self.status == 'completed':
            if not self.can_retake:
                return False
            
            if self.next_retake_date and timezone.now() < self.next_retake_date:
                return False
        
        return self.status in ['pending', 'expired', 'cancelled']
    
    def get_remaining_time(self):
        """Получить оставшееся время теста в секундах"""
        if self.status != 'in_progress' or not self.started_at:
            return 0
        
        elapsed = (timezone.now() - self.started_at).total_seconds()
        remaining = (self.time_limit_minutes * 60) - elapsed - self.time_spent_seconds
        
        return max(0, remaining)