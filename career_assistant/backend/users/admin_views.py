from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import User
from .admin_serializers import (
    AdminUserSerializer, 
    AdminUserUpdateSerializer,
    AdminStatsSerializer
)
from resumes.models import Resume  # если есть
from applications.models import Application  # если есть
from vacancies.models import Vacancy  # если есть


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class AdminUserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserSerializer
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Фильтрация
        search = self.request.query_params.get('search', '')
        is_active = self.request.query_params.get('is_active', None)
        
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def get(self, request, *args, **kwargs):
        # Проверка прав
        if not request.user.is_superuser:
            return Response(
                {'error': 'You do not have permission to access this resource'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().get(request, *args, **kwargs)


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserUpdateSerializer
        return AdminUserSerializer


class AdminToggleUserActiveView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
            
            return Response({
                'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
                'is_active': user.is_active
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        today = timezone.now().date()
        
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'new_users_today': User.objects.filter(date_joined__date=today).count(),
        }
        
        # Добавляем данные из других приложений, если они существуют
        try:
            from resumes.models import Resume
            stats['total_resumes'] = Resume.objects.count()
        except:
            stats['total_resumes'] = 0
        
        try:
            from applications.models import Application
            stats['total_applications'] = Application.objects.count()
        except:
            stats['total_applications'] = 0
        
        try:
            from vacancies.models import Vacancy
            stats['active_vacancies'] = Vacancy.objects.filter(is_active=True).count()
        except:
            stats['active_vacancies'] = 0
        
        serializer = AdminStatsSerializer(stats)
        return Response(serializer.data)