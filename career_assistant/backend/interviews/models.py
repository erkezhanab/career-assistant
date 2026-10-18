from django.db import models
from users.models import User
from resumes.models import Resume


class Interview(models.Model):
    TYPE_CHOICES = [
        ('hr', 'HR интервью'),
        ('technical', 'Техническое'),
        ('stress', 'Стресс'),
        ('behavioral', 'Поведенческое'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interviews')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    questions = models.JSONField()  # List of questions
    answers = models.JSONField(default=list, blank=True)  # User answers
    feedback = models.JSONField(default=dict, blank=True)  # AI feedback
    preparation_tips = models.TextField(blank=True)
    duration_minutes = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_interview_type_display()} for {self.user.email}"