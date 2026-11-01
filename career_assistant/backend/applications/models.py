"""
Модели приложения applications — отклики пользователя на вакансии.

Ответственность модуля:
  - Application — факт отклика: кто, на какую вакансию, с каким резюме
                  и каким сопроводительным письмом откликнулся.
"""

from django.db import models
from users.models import User
from vacancies.models import Vacancy
from resumes.models import Resume


class Application(models.Model):
    """
    Отклик на вакансию.

    Связывает три сущности: пользователя, вакансию и резюме.
    Хранит сгенерированное ИИ сопроводительное письмо и статус рассмотрения.
    """

    # Статусы отклика — отображаются пользователю в списке "Мои отклики"
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('viewed', 'Просмотрено'),
        ('rejected', 'Отклонено'),
        ('invited', 'Приглашение'),
    ]

    # Три внешних ключа = отклик имеет смысл только вместе с ними.
    # CASCADE: удалили пользователя/вакансию/резюме — отклик тоже удаляется,
    # чтобы в базе не оставалось "висячих" записей.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='applications')

    # Текст письма (сгенерирован ИИ, пользователь мог отредактировать перед отправкой)
    cover_letter = models.TextField()

    # Стиль, в котором ИИ писал письмо — передаётся в ClaudeService
    letter_style = models.CharField(
        max_length=20,
        choices=[
            ('formal', 'Официальный'),
            ('friendly', 'Дружелюбный'),
            ('brief', 'Краткий'),
            ('creative', 'Креативный'),
        ]
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    applied_at = models.DateTimeField(auto_now_add=True)  # дата отклика
    updated_at = models.DateTimeField(auto_now=True)      # дата смены статуса

    class Meta:
        # Защита от повторного отклика: на одну вакансию один пользователь
        # может откликнуться только один раз (ограничение на уровне БД)
        unique_together = ['user', 'vacancy']

    def __str__(self):
        return f"{self.user.email} -> {self.vacancy.name}"
