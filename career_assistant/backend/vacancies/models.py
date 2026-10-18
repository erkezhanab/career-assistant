from django.db import models
from users.models import User


class Vacancy(models.Model):
    hh_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    salary_from = models.IntegerField(null=True, blank=True)
    salary_to = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField()
    requirements = models.TextField()
    experience = models.CharField(max_length=100, null=True, blank=True)
    employment_type = models.CharField(max_length=100, null=True, blank=True)
    schedule = models.CharField(max_length=100, null=True, blank=True)
    skills = models.JSONField(default=list)
    url = models.URLField()
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Vacancies'
        ordering = ['-published_at']
    
    def __str__(self):
        return f"{self.name} at {self.company}"


class SearchQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries')
    position = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    salary_desired = models.IntegerField(null=True, blank=True)
    programming_languages = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.position} in {self.city}"