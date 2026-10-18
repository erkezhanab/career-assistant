from rest_framework import serializers
from .models import Vacancy, SearchQuery

class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = '__all__'

class SearchQuerySerializer(serializers.Serializer):
    position = serializers.CharField(required=True, allow_blank=False, min_length=2)
    city = serializers.CharField(required=False, allow_blank=True, min_length=0, default='')
    salary_desired = serializers.IntegerField(required=False, min_value=0, allow_null=True)
    programming_languages = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
