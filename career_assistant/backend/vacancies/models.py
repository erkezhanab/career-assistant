"""
Модели приложения vacancies — вакансии и история поисковых запросов.

Ответственность модуля:
  - Vacancy     — вакансия (загруженная с HeadHunter или добавленная в базу)
  - SearchQuery — лог того, что и где искал пользователь
"""

from django.db import models
from users.models import User


class Vacancy(models.Model):
    """
    Вакансия.

    Источник данных — API HeadHunter (или демо-данные при недоступности API).
    Вакансии кешируются в своей базе, чтобы:
      1) не дёргать внешний API на каждый просмотр;
      2) можно было ссылаться на вакансию из отклика (Application).
    """

    # Идентификатор вакансии в системе HeadHunter.
    # unique=True — защита от дублей при повторной загрузке одной и той же вакансии.
    # db_index=True — индекс в БД, ускоряет поиск по hh_id (используется в update_or_create).
    hh_id = models.IntegerField(unique=True, db_index=True)

    name = models.CharField(max_length=255)      # должность
    company = models.CharField(max_length=255)   # работодатель
    city = models.CharField(max_length=100)      # город (по нему идёт фильтрация поиска)

    # Зарплата может быть не указана вообще или указана только "от"/"до",
    # поэтому все три поля необязательные (null=True)
    salary_from = models.IntegerField(null=True, blank=True)
    salary_to = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, null=True, blank=True)  # KZT, RUB, USD

    description = models.TextField()   # полное описание (приходит с HTML-разметкой)
    requirements = models.TextField()  # требования к кандидату

    experience = models.CharField(max_length=100, null=True, blank=True)       # "От 1 года до 3 лет"
    employment_type = models.CharField(max_length=100, null=True, blank=True)  # "Полная занятость"
    schedule = models.CharField(max_length=100, null=True, blank=True)         # "Удаленная работа"

    # JSONField — список навыков хранится прямо в одном поле как массив
    # (["Python", "Django"]), отдельная таблица для навыков не нужна
    skills = models.JSONField(default=list)

    url = models.URLField()                  # ссылка на вакансию для кнопки "На HH.ru"
    published_at = models.DateTimeField()    # когда вакансия опубликована работодателем

    created_at = models.DateTimeField(auto_now_add=True)  # когда попала в нашу базу
    updated_at = models.DateTimeField(auto_now=True)      # когда последний раз обновлялась

    class Meta:
        verbose_name_plural = 'Vacancies'   # правильное множественное число в админке
        ordering = ['-published_at']        # по умолчанию сортировка: сначала свежие

    def __str__(self):
        return f"{self.name} at {self.company}"


class SearchQuery(models.Model):
    """
    История поисковых запросов пользователя.

    Сохраняется при каждом поиске. Нужна для аналитики
    (что ищут пользователи) и для будущих автоподборок вакансий.
    """

    # ForeignKey — у одного пользователя много запросов (связь один-ко-многим)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries')

    position = models.CharField(max_length=255)  # искомая должность
    city = models.CharField(max_length=100)      # город поиска

    salary_desired = models.IntegerField(null=True, blank=True)  # желаемая зарплата "от"
    programming_languages = models.JSONField(default=list)       # выбранные языки-фильтры

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.position} in {self.city}"
