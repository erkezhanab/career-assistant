from rest_framework import serializers
from .models import Interview


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'id', 'resume', 'interview_type', 'questions',
            'answers', 'preparation_tips', 'feedback',
            'duration_minutes', 'created_at', 'completed', 
            'completed_at'
        ]
        read_only_fields = ['user', 'questions', 'preparation_tips', 
                          'feedback', 'created_at', 'completed_at']


class InterviewRequestSerializer(serializers.Serializer):
    interview_type = serializers.ChoiceField(
        choices=[
            ('hr', 'HR интервью'),
            ('technical', 'Техническое'),
            ('stress', 'Стресс'),
            ('behavioral', 'Поведенческое'),
        ],
        required=True
    )
    vacancy_id = serializers.IntegerField(required=False)


class CompleteInterviewSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )