from rest_framework import serializers
from django.utils import timezone
from .models import TestCategory, TestQuestion, UserCertificate, TestSession
import json


class TestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCategory
        fields = ['id', 'name', 'description']


class TestQuestionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = TestQuestion
        fields = [
            'id', 'category', 'category_name', 'question_type', 
            'question_text', 'options', 'difficulty', 'time_limit_seconds',
            'explanation'
        ]


class UserCertificateSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserCertificate
        fields = [
            'id', 'title', 'issuer', 'document_type', 'issue_date', 'expiry_date', 'description',
            'document_file', 'file_url', 'file_size', 'file_type', 'is_verified', 'created_at'
        ]
        read_only_fields = ['file_size', 'file_type', 'is_verified', 'user', 'created_at', 'file_url']
    
    def get_file_url(self, obj):
        """Получить абсолютный URL файла"""
        if obj.document_file and hasattr(obj.document_file, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.document_file.url)
            return obj.document_file.url
        return None
    
    def validate_issue_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Дата выдачи не может быть в будущем")
        return value
    
    def validate(self, data):
        if data.get('expiry_date') and data['expiry_date'] < data['issue_date']:
            raise serializers.ValidationError({
                'expiry_date': 'Дата окончания действия не может быть раньше даты выдачи'
            })
        return data


class TestSessionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
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
        read_only_fields = ['user', 'score', 'correct_count', 'incorrect_count', 
                           'can_retake', 'next_retake_date', 'detailed_results']


class StartTestSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    question_count = serializers.IntegerField(default=15, min_value=5, max_value=50, required=False)


class FlexibleAnswerField(serializers.Field):
    """Гибкое поле для ответа, принимающее любые данные"""
    
    def to_representation(self, value):
        """Преобразование для сериализации"""
        return value
    
    def to_internal_value(self, data):
        """Преобразование для десериализации"""
        if isinstance(data, list):
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
    answer = FlexibleAnswerField(required=True)


class CompleteTestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=True)


class TestResultSerializer(serializers.ModelSerializer):
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
        return obj.score >= obj.passing_score if obj.score else False


class SimpleStartTestSerializer(serializers.Serializer):
    """Упрощенный сериализатор для начала теста"""
    category_id = serializers.IntegerField(required=False, allow_null=True)
    question_count = serializers.IntegerField(default=10, min_value=5, max_value=50)
    
    def validate(self, data):
        return data