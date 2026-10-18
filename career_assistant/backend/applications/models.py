from django.db import models
from users.models import User
from vacancies.models import Vacancy
from resumes.models import Resume


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('viewed', 'Просмотрено'),
        ('rejected', 'Отклонено'),
        ('invited', 'Приглашение'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField()
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
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'vacancy']
    
    def __str__(self):
        return f"{self.user.email} -> {self.vacancy.name}"