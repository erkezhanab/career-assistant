"""
Сериализаторы приложения vacancies.

  - VacancySerializer     — вакансия в формате JSON для фронтенда
  - SearchQuerySerializer — проверка параметров поискового запроса
"""

from rest_framework import serializers
from .models import Vacancy, SearchQuery


class VacancySerializer(serializers.ModelSerializer):
    """Вакансия целиком. Используется во всех ответах с вакансиями."""

    class Meta:
        model = Vacancy
        # '__all__' — отдаём все поля модели. Здесь это безопасно:
        # вакансии публичны и не содержат личных данных пользователей
        fields = '__all__'


class SearchQuerySerializer(serializers.Serializer):
    """
    Проверка параметров поиска вакансий.

    Задача — не пустить в поиск некорректные данные: например,
    запрос из одной буквы или отрицательную зарплату.
    """

    # Должность обязательна: без неё искать нечего.
    # min_length=2 отсекает бессмысленные запросы из одного символа
    position = serializers.CharField(required=True, allow_blank=False, min_length=2)

    # Город необязателен — поиск может идти по всем городам.
    # default='' избавляет views от проверок на отсутствие поля
    city = serializers.CharField(required=False, allow_blank=True, min_length=0, default='')

    # min_value=0 не даёт передать отрицательную зарплату
    salary_desired = serializers.IntegerField(required=False, min_value=0, allow_null=True)

    # Список выбранных языков программирования.
    # default=list — если поле не передали, подставится пустой список
    programming_languages = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
