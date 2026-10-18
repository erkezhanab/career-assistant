from rest_framework import serializers
from .models import User, UserProfile

class AdminUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    resume_count = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone', 
            'specialization', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'profile', 'resume_count',
            'application_count'
        )
        read_only_fields = ('date_joined', 'last_login')
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'notifications_enabled': profile.notifications_enabled,
                'search_frequency': profile.search_frequency,
                'email_notifications': profile.email_notifications,
                'created_at': profile.created_at,
                'updated_at': profile.updated_at
            }
        except UserProfile.DoesNotExist:
            return None
    
    def get_resume_count(self, obj):
        # Предполагаем, что есть модель Resume
        from resumes.models import Resume  # если такая модель есть
        return Resume.objects.filter(user=obj).count() if hasattr(obj, 'resume_set') else 0
    
    def get_application_count(self, obj):
        # Предполагаем, что есть модель Application
        from applications.models import Application  # если такая модель есть
        return Application.objects.filter(user=obj).count() if hasattr(obj, 'application_set') else 0


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'specialization', 'is_active')


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    total_resumes = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    active_vacancies = serializers.IntegerField()