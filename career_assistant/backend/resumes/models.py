"""
Модели приложения resumes — резюме пользователя и результаты их ИИ-анализа.

Ответственность модуля:
  - Resume — загруженный файл резюме + извлечённый из него текст
             + оценка и рекомендации, полученные от ИИ.
"""

import os
from django.db import models
from django.core.validators import FileExtensionValidator
from users.models import User


class Resume(models.Model):
    """
    Резюме пользователя.

    Жизненный цикл записи:
      1. Пользователь загружает файл (PDF/DOC/DOCX) -> status='pending'
      2. Из файла извлекается текст (PyPDF2 / python-docx) -> extracted_text
      3. Текст уходит в ИИ на анализ (в фоновом потоке)
      4. Результат раскладывается по полям ниже -> status='approved'/'rejected'
    """

    STATUS_CHOICES = [
        ('pending', 'На проверке'),        # загружено, ИИ ещё анализирует
        ('approved', 'Одобрено'),          # оценка >= 6 баллов
        ('rejected', 'Требует доработки'), # оценка < 6 баллов
        ('failed', 'Ошибка анализа'),      # ИИ недоступен / файл не прочитался
    ]

    # У одного пользователя может быть несколько резюме (например, под разные профессии)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')

    file = models.FileField(
        # Файлы раскладываются по папкам с датой: media/resumes/2026/11/01/
        upload_to='resumes/%Y/%m/%d/',
        # Валидатор не даст загрузить .exe или картинку — только документы
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        max_length=255
    )

    # Имя файла, как его назвал пользователь (на диске имя может отличаться)
    original_filename = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # --- Результаты анализа ИИ ---

    # Полный JSON-ответ ИИ целиком (на случай, если понадобятся поля,
    # которые не разложены по отдельным колонкам ниже)
    analysis_result = models.JSONField(null=True, blank=True)

    overall_score = models.FloatField(null=True, blank=True)  # общая оценка резюме (1-10)

    # Списки от ИИ сохраняются как текст, элементы разделены переносом строки
    strong_points = models.TextField(blank=True)    # сильные стороны
    improvements = models.TextField(blank=True)     # что улучшить
    recommendations = models.TextField(blank=True)  # что добавить

    analyzed_at = models.DateTimeField(null=True, blank=True)  # когда ИИ закончил анализ

    # --- Данные, извлечённые из файла ---

    # Текст резюме. Используется повторно: для генерации сопроводительных писем,
    # вопросов на интервью и персональных тестов
    extracted_text = models.TextField(blank=True)

    skills = models.JSONField(default=list, blank=True)        # ["Python", "Django", ...]
    experience_years = models.IntegerField(null=True, blank=True)
    education = models.JSONField(default=list, blank=True)     # [{"degree": ..., "institution": ...}]

    class Meta:
        ordering = ['-upload_date']  # в списке сначала самые свежие резюме

    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"

    def delete(self, *args, **kwargs):
        """
        Переопределён, чтобы вместе с записью из БД удалялся и сам файл с диска.

        Без этого файлы накапливались бы в папке media/ навсегда ("мусор"),
        так как Django по умолчанию удаляет только строку в базе.
        """
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
