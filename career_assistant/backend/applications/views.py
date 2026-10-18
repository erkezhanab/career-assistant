from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Application
from .serializers import ApplicationSerializer, CoverLetterRequestSerializer
from resumes.models import Resume
from vacancies.models import Vacancy
from core.services.gemini_service import GeminiService


class ApplyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        vacancy_id = request.data.get('vacancy_id')
        cover_letter = request.data.get('cover_letter')
        letter_style = request.data.get('letter_style', 'formal')
        
        if not vacancy_id or not cover_letter:
            return Response(
                {'error': 'Vacancy ID and cover letter are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vacancy = get_object_or_404(Vacancy, id=vacancy_id)
        
        resume = Resume.objects.filter(
            user=request.user,
            status='approved'
        ).first()
        
        if not resume:
            return Response(
                {'error': 'No approved resume found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application = Application.objects.create(
            user=request.user,
            vacancy=vacancy,
            resume=resume,
            cover_letter=cover_letter,
            letter_style=letter_style
        )
        
        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )


class GenerateCoverLetterView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CoverLetterRequestSerializer(data=request.data)
        if serializer.is_valid():
            vacancy_id = serializer.validated_data['vacancy_id']
            style = serializer.validated_data['style']
            
            vacancy = get_object_or_404(Vacancy, id=vacancy_id)
            resume = Resume.objects.filter(
                user=request.user,
                status='approved'
            ).first()
            
            if not resume:
                return Response(
                    {'error': 'No approved resume found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Генерируем сопроводительное письмо через Gemini
            gemini = GeminiService()
            cover_letter = gemini.generate_cover_letter(
                resume.extracted_text,
                vacancy.description,
                style
            )
            
            return Response({'letter': cover_letter})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).order_by('-applied_at')


class ApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)