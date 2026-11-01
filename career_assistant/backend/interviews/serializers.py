"""
Сериализаторы приложения interviews.

  - InterviewSerializer         — данные пробного собеседования
  - InterviewRequestSerializer  — проверка запроса на создание интервью
  - CompleteInterviewSerializer — проверка ответов пользователя
"""

from rest_framework import serializers
from .models import Interview


class InterviewSerializer(serializers.ModelSerializer):
    """Пробное собеседование целиком: вопросы, ответы и разбор."""

    class Meta:
        model = Interview
        fields = [
            'id', 'resume', 'interview_type', 'questions',
            'answers', 'preparation_tips', 'feedback',
            'duration_minutes', 'created_at', 'completed',
            'completed_at'
        ]
        # Вопросы и разбор создаёт ИИ, поэтому изменять их нельзя.
        # Открытым остаётся поле answers — именно его присылает
        # пользователь, отвечая на вопросы
        read_only_fields = ['user', 'questions', 'preparation_tips',
                          'feedback', 'created_at', 'completed_at']


class InterviewRequestSerializer(serializers.Serializer):
    """Запрос на создание интервью: какой тип и под какую вакансию."""

    # ChoiceField гарантирует, что тип интервью будет одним из четырёх —
    # сервис ИИ получит корректное значение и не выдаст ошибку
    interview_type = serializers.ChoiceField(
        choices=[
            ('hr', 'HR интервью'),
            ('technical', 'Техническое'),
            ('stress', 'Стресс'),
            ('behavioral', 'Поведенческое'),
        ],
        required=True
    )
    # Вакансия необязательна: можно тренироваться «вообще»,
    # без привязки к конкретной позиции
    vacancy_id = serializers.IntegerField(required=False)


class CompleteInterviewSerializer(serializers.Serializer):
    """Проверка ответов при завершении интервью."""

    # ListField со строками внутри: ожидается массив ответов
    # в том же порядке, в каком шли вопросы
    answers = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )
