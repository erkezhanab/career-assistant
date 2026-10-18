from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    vacancy_name = serializers.CharField(source='vacancy.name', read_only=True)
    company_name = serializers.CharField(source='vacancy.company', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'vacancy', 'vacancy_name', 'company_name',
            'cover_letter', 'letter_style', 'status',
            'applied_at', 'updated_at'
        ]
        read_only_fields = ['user', 'resume', 'status', 'applied_at', 'updated_at']


class CoverLetterRequestSerializer(serializers.Serializer):
    vacancy_id = serializers.IntegerField(required=True)
    style = serializers.ChoiceField(
        choices=[
            ('formal', 'Официальный'),
            ('friendly', 'Дружелюбный'),
            ('brief', 'Краткий'),
            ('creative', 'Креативный'),
        ],
        default='formal'
    )