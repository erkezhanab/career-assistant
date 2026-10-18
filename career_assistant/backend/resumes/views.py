import PyPDF2
from docx import Document
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import Resume
from .serializers import ResumeSerializer, ResumeAnalysisSerializer
from core.services.gemini_service import GeminiService
from rest_framework import serializers
import threading
import logging

logger = logging.getLogger(__name__)


class ResumeUploadView(generics.CreateAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def extract_text_from_file(self, file):
        """Извлечение текста из PDF или DOCX"""
        text = ""
        
        try:
            logger.info(f"Extracting text from file: {file.name}, type: {file.content_type}")
            
            if file.name.lower().endswith('.pdf'):
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            elif file.name.lower().endswith(('.doc', '.docx')):
                doc = Document(file)
                for paragraph in doc.paragraphs:
                    if paragraph.text:
                        text += paragraph.text + '\n'
            
            logger.info(f"Extracted {len(text)} characters from file")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from {file.name}: {str(e)}")
            return ""
    
    def perform_create(self, serializer):
        file = self.request.FILES.get('file')
        if not file:
            logger.error("No file in request")
            raise serializers.ValidationError({"file": "Файл не передан"})
        
        logger.info(f"Processing file: {file.name}, size: {file.size}, type: {file.content_type}")
        
        # Извлекаем текст ДО сохранения в БД
        extracted_text = self.extract_text_from_file(file)
        if not extracted_text or len(extracted_text.strip()) < 10:
            logger.error(f"Failed to extract text from file or text too short: {len(extracted_text)} chars")
            raise serializers.ValidationError({"file": "Не удалось извлечь текст из файла или файл слишком короткий"})
        
        # Сохраняем резюме
        resume = serializer.save(
            user=self.request.user,
            original_filename=file.name,
            extracted_text=extracted_text  # Сохраняем текст сразу
        )
        
        logger.info(f"Resume created: {resume.id}, user: {resume.user.email}")
        
        # Запускаем анализ в фоновом режиме
        self.analyze_resume(resume.id)
        
        return resume
    
    def create(self, request, *args, **kwargs):
        logger.info(f"Upload request received. User: {request.user.email}")
        logger.info(f"FILES: {dict(request.FILES)}")
        logger.info(f"DATA: {dict(request.data)}")
        
        try:
            # Проверяем наличие файла
            if 'file' not in request.FILES:
                logger.error("No 'file' key in request.FILES")
                return Response(
                    {"file": "Файл не передан"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = self.perform_create(serializer)
            
            return Response(
                ResumeSerializer(instance).data,
                status=status.HTTP_201_CREATED
            )
            
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.exception(f"Unexpected error in resume upload: {str(e)}")
            return Response(
                {"error": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def analyze_resume(self, resume_id):
        """Анализ резюме в фоне"""
        
        def analyze():
            try:
                logger.info(f"Starting analysis for resume {resume_id}")
                resume = Resume.objects.get(id=resume_id)
                
                # Обновляем статус на "в процессе анализа"
                resume.status = 'pending'
                resume.save()
                
                gemini = GeminiService()
                
                # Получаем специализацию пользователя, если есть
                specialization = None
                if hasattr(resume.user, 'specialization') and resume.user.specialization:
                    specialization = resume.user.specialization
                
                analysis = gemini.analyze_resume(
                    resume.extracted_text,
                    specialization
                )
                
                # Обновляем поля резюме
                resume.analysis_result = analysis
                resume.overall_score = analysis.get('overall_score', 5.0)
                
                # Преобразуем списки в строки
                strong_points = analysis.get('strong_points', [])
                improvements = analysis.get('improvements', [])
                recommendations = analysis.get('additions', [])
                
                resume.strong_points = '\n'.join(strong_points) if isinstance(strong_points, list) else str(strong_points)
                resume.improvements = '\n'.join(improvements) if isinstance(improvements, list) else str(improvements)
                resume.recommendations = '\n'.join(recommendations) if isinstance(recommendations, list) else str(recommendations)
                
                resume.analyzed_at = timezone.now()
                
                # Определяем статус на основе оценки
                if resume.overall_score >= 6.0:
                    resume.status = 'approved'
                else:
                    resume.status = 'rejected'
                
                resume.save()
                logger.info(f"Analysis completed for resume {resume_id}, score: {resume.overall_score}, status: {resume.status}")
                
            except Resume.DoesNotExist:
                logger.error(f"Resume {resume_id} not found")
            except Exception as e:
                logger.error(f"Error analyzing resume {resume_id}: {str(e)}")
                # Обновляем статус как "failed"
                try:
                    resume = Resume.objects.get(id=resume_id)
                    resume.status = 'failed'
                    resume.save()
                    logger.info(f"Resume {resume_id} status set to 'failed'")
                except:
                    pass
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=analyze)
        thread.daemon = True
        thread.start()
        logger.info(f"Analysis thread started for resume {resume_id}")


class ResumeAnalysisView(generics.RetrieveAPIView):
    serializer_class = ResumeAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        resume_id = self.kwargs['pk']
        try:
            return Resume.objects.get(id=resume_id, user=self.request.user)
        except Resume.DoesNotExist:
            raise serializers.ValidationError({"error": "Резюме не найдено"})


class ResumeDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


class UserResumesView(generics.ListAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by('-upload_date')