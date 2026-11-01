"""
Сериализаторы приложения testing.

  - TestCategorySerializer     — категория теста
  - TestQuestionSerializer     — вопрос БЕЗ правильного ответа
  - UserCertificateSerializer  — документ пользователя с проверкой дат
  - TestSessionSerializer      — сессия тестирования
  - FlexibleAnswerField        — поле, принимающее ответ любого вида
  - SubmitAnswerSerializer     — отправка ответа
  - TestResultSerializer       — итоговый результат с разбором
"""

from rest_framework import serializers
from django.utils import timezone
from .models import TestCategory, TestQuestion, UserCertificate, TestSession
import json


class TestCategorySerializer(serializers.ModelSerializer):
    """Направление тестирования для выпадающего списка на странице."""

    class Meta:
        model = TestCategory
        fields = ['id', 'name', 'description']


class TestQuestionSerializer(serializers.ModelSerializer):
    """
    Вопрос теста для показа пользователю.

    ВАЖНО: поле correct_answer намеренно отсутствует в списке fields.
    Если бы оно отдавалось, правильный ответ было бы видно
    в инструментах разработчика браузера — тест потерял бы смысл.
    """

    # Название категории подставляется из связанной модели,
    # чтобы не делать отдельный запрос за ней
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = TestQuestion
        fields = [
            'id', 'category', 'category_name', 'question_type',
            'question_text', 'options', 'difficulty', 'time_limit_seconds',
            'explanation'
        ]


class UserCertificateSerializer(serializers.ModelSerializer):
    """Документ пользователя (диплом, сертификат, курс) с проверкой дат."""

    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserCertificate
        fields = [
            'id', 'title', 'issuer', 'document_type', 'issue_date', 'expiry_date', 'description',
            'document_file', 'file_url', 'file_size', 'file_type', 'is_verified', 'created_at'
        ]
        # is_verified закрыт от правки: подтверждать документ
        # вправе только администратор, а не сам пользователь.
        # file_size и file_type вычисляются автоматически в модели
        read_only_fields = ['file_size', 'file_type', 'is_verified', 'user', 'created_at', 'file_url']

    def get_file_url(self, obj):
        """Получить абсолютный URL файла"""
        # Нужен полный адрес (http://localhost:8000/media/...), так как
        # React работает на другом порту и относительный путь не откроется
        if obj.document_file and hasattr(obj.document_file, 'url'):
            request = self.context.get('request')
            if request is not None:
                # build_absolute_uri добавляет протокол и домен
                return request.build_absolute_uri(obj.document_file.url)
            # Запроса в контексте нет — отдаём относительный путь
            return obj.document_file.url
        return None

    def validate_issue_date(self, value):
        """Проверка одного поля: дата выдачи."""
        # Документ не может быть выдан в будущем
        if value > timezone.now().date():
            raise serializers.ValidationError("Дата выдачи не может быть в будущем")
        return value

    def validate(self, data):
        """Проверка связи двух полей между собой."""
        # Сравнение дат возможно, только если срок окончания указан
        if data.get('expiry_date') and data['expiry_date'] < data['issue_date']:
            raise serializers.ValidationError({
                'expiry_date': 'Дата окончания действия не может быть раньше даты выдачи'
            })
        return data


class TestSessionSerializer(serializers.ModelSerializer):
    """Сессия тестирования: состояние попытки и её результат."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    # Значение берётся из метода модели get_remaining_time() — для таймера
    remaining_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = TestSession
        fields = [
            'id', 'user', 'category', 'category_name', 'status',
            'total_questions', 'score', 'passing_score', 'time_limit_minutes',
            'started_at', 'completed_at', 'time_spent_seconds', 'correct_count',
            'incorrect_count', 'can_retake', 'next_retake_date', 'remaining_time',
            'created_at', 'updated_at'
        ]
        # Все поля результата закрыты от изменения: их считает сервер.
        # Иначе можно было бы отправить себе score = 100
        read_only_fields = ['user', 'score', 'correct_count', 'incorrect_count',
                           'can_retake', 'next_retake_date', 'detailed_results']


class StartTestSerializer(serializers.Serializer):
    """Параметры запуска теста."""

    category_id = serializers.IntegerField(required=False, allow_null=True)
    # Границы 5-50 защищают от запроса в 10 000 вопросов,
    # который перегрузил бы ИИ и базу
    question_count = serializers.IntegerField(default=15, min_value=5, max_value=50, required=False)


class FlexibleAnswerField(serializers.Field):
    """Гибкое поле для ответа, принимающее любые данные"""

    # Обычные поля DRF требуют конкретный тип, а ответ может быть
    # строкой (один вариант), списком (несколько вариантов)
    # или текстом. Поэтому поле описано вручную

    def to_representation(self, value):
        """Преобразование для сериализации"""
        # Из базы наружу значение отдаётся как есть
        return value

    def to_internal_value(self, data):
        """Преобразование для десериализации"""
        # Всё приводится к строке, потому что user_answers хранится
        # в JSON-поле, а проверка ответов в модели сравнивает строки
        if isinstance(data, list):
            # ensure_ascii=False сохраняет русские буквы читаемыми
            return json.dumps(data, ensure_ascii=False)
        elif isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False)
        elif isinstance(data, (int, float)):
            return str(data)
        elif isinstance(data, bool):
            return str(data).lower()
        elif isinstance(data, str):
            return data
        else:
            return str(data)


class SubmitAnswerSerializer(serializers.Serializer):
    """Упрощенный сериализатор для отправки ответа"""

    session_id = serializers.IntegerField(required=True)
    question_id = serializers.IntegerField(required=True)
    # Своё поле, так как тип ответа зависит от типа вопроса
    answer = FlexibleAnswerField(required=True)


class CompleteTestSerializer(serializers.Serializer):
    """Завершение теста: достаточно номера сессии."""

    session_id = serializers.IntegerField(required=True)


class TestResultSerializer(serializers.ModelSerializer):
    """Итоговый результат теста с подробным разбором ответов."""

    # Разбор по каждому вопросу: что спросили, что ответил,
    # как правильно и почему
    detailed_results = serializers.JSONField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    passed = serializers.SerializerMethodField()

    class Meta:
        model = TestSession
        fields = [
            'id', 'category', 'category_name', 'score', 'passing_score',
            'correct_count', 'incorrect_count', 'total_questions',
            'time_spent_seconds', 'detailed_results', 'passed',
            'can_retake', 'next_retake_date', 'completed_at'
        ]

    def get_passed(self, obj):
        """Сдан ли тест: балл не ниже проходного."""
        # Проверка «if obj.score» нужна, потому что у незавершённого
        # теста балла нет (None), а сравнивать None с числом нельзя
        return obj.score >= obj.passing_score if obj.score else False


class SimpleStartTestSerializer(serializers.Serializer):
    """Упрощенный сериализатор для начала теста"""

    category_id = serializers.IntegerField(required=False, allow_null=True)
    question_count = serializers.IntegerField(default=10, min_value=5, max_value=50)

    def validate(self, data):
        return data
