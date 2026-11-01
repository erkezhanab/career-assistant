"""
Сериализаторы приложения applications.

  - ApplicationSerializer         — отклик для отображения в списке
  - CoverLetterRequestSerializer  — проверка запроса на генерацию письма
"""

from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Отклик на вакансию.

    Дополнительно подставляет название вакансии и компании, чтобы
    фронтенд мог показать список откликов одним запросом,
    не запрашивая каждую вакансию отдельно.
    """

    # source='vacancy.name' — значение берётся из связанной модели Vacancy.
    # read_only: это справочные данные, изменять их через отклик нельзя
    vacancy_name = serializers.CharField(source='vacancy.name', read_only=True)
    company_name = serializers.CharField(source='vacancy.company', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'vacancy', 'vacancy_name', 'company_name',
            'cover_letter', 'letter_style', 'status',
            'applied_at', 'updated_at'
        ]
        # Эти поля заполняет сервер. Особенно важен user:
        # без запрета можно было бы создать отклик от чужого имени.
        # Статус тоже закрыт — иначе пользователь сам поставил бы
        # себе «Приглашение»
        read_only_fields = ['user', 'resume', 'status', 'applied_at', 'updated_at']


class CoverLetterRequestSerializer(serializers.Serializer):
    """
    Проверка данных для генерации сопроводительного письма.

    Не связан с моделью: письмо нигде не сохраняется до отправки отклика,
    поэтому нужен обычный Serializer, а не ModelSerializer.
    """

    vacancy_id = serializers.IntegerField(required=True)

    # ChoiceField допускает только перечисленные значения — произвольный
    # стиль отправить не получится, ИИ всегда получит корректный параметр
    style = serializers.ChoiceField(
        choices=[
            ('formal', 'Официальный'),
            ('friendly', 'Дружелюбный'),
            ('brief', 'Краткий'),
            ('creative', 'Креативный'),
        ],
        default='formal'
    )
