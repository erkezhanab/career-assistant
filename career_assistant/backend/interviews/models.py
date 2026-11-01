"""
Модели приложения interviews — тренировочные собеседования с ИИ.

Ответственность модуля:
  - Interview — одна сессия пробного интервью: сгенерированные ИИ вопросы,
                ответы пользователя и итоговый разбор (фидбек) от ИИ.
"""

from django.db import models
from users.models import User
from resumes.models import Resume


class Interview(models.Model):
    """
    Пробное собеседование.

    Сценарий работы:
      1. Пользователь выбирает тип интервью -> ИИ по его резюме генерирует вопросы
      2. Пользователь отвечает на вопросы -> ответы сохраняются в answers
      3. Ответы уходят в ИИ -> возвращается разбор, который ложится в feedback
    """

    # Типы интервью — от выбранного типа зависит характер вопросов,
    # которые сгенерирует ИИ (см. ClaudeService.generate_interview_questions)
    TYPE_CHOICES = [
        ('hr', 'HR интервью'),           # мотивация, карьерные цели
        ('technical', 'Техническое'),    # вопросы по технологиям
        ('stress', 'Стресс'),            # провокационные вопросы
        ('behavioral', 'Поведенческое'), # ситуации из прошлого опыта
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interviews')

    # Резюме, на основе которого ИИ придумывал вопросы:
    # благодаря этому вопросы персональные, а не шаблонные
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='interviews')

    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Список вопросов от ИИ:
    # [{"question": "...", "category": "...", "tips": "..."}]
    questions = models.JSONField()

    # Ответы пользователя в том же порядке, что и вопросы: ["ответ1", "ответ2", ...]
    answers = models.JSONField(default=list, blank=True)

    # Разбор от ИИ: оценка, сильные/слабые стороны, советы
    # {"overall_score": 7.5, "strengths": [...], "weaknesses": [...], ...}
    feedback = models.JSONField(default=dict, blank=True)

    preparation_tips = models.TextField(blank=True)   # советы по подготовке
    duration_minutes = models.IntegerField(default=60)

    created_at = models.DateTimeField(auto_now_add=True)

    completed = models.BooleanField(default=False)    # пользователь дошёл до конца?
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        # get_interview_type_display() — метод Django: возвращает не 'hr',
        # а читаемое название из TYPE_CHOICES ("HR интервью")
        return f"{self.get_interview_type_display()} for {self.user.email}"
