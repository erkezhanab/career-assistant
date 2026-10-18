import os
from django.db import models
from django.core.validators import FileExtensionValidator
from users.models import User


class Resume(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Одобрено'),
        ('rejected', 'Требует доработки'),
        ('failed', 'Ошибка анализа'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(
        upload_to='resumes/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        max_length=255
    )
    original_filename = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    analysis_result = models.JSONField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)
    strong_points = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    
    extracted_text = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    education = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"
    
    def delete(self, *args, **kwargs):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)