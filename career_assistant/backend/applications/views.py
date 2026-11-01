"""
Представления (views) приложения applications — отклики на вакансии.

  - ApplyView               — отправить отклик на вакансию
  - GenerateCoverLetterView — сгенерировать сопроводительное письмо через ИИ
  - ApplicationListView     — список моих отправленных откликов
  - ApplicationDetailView   — один отклик подробно
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Application
from .serializers import ApplicationSerializer, CoverLetterRequestSerializer
from resumes.models import Resume
from vacancies.models import Vacancy
from core.services.claude_service import ClaudeService


class ApplyView(APIView):
    """
    Отправка отклика на вакансию.  POST /api/applications/apply/

    Принимает id вакансии и текст письма, создаёт запись Application.
    Резюме подставляется автоматически — берётся последнее одобренное.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        vacancy_id = request.data.get('vacancy_id')
        cover_letter = request.data.get('cover_letter')
        # Второй аргумент .get() — значение по умолчанию, если стиль не передан
        letter_style = request.data.get('letter_style', 'formal')

        # Проверка обязательных полей: без вакансии и письма отклик бессмысленен
        if not vacancy_id or not cover_letter:
            return Response(
                {'error': 'Vacancy ID and cover letter are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # get_object_or_404 сам вернёт ошибку 404, если вакансии нет в базе —
        # не нужно писать проверку вручную
        vacancy = get_object_or_404(Vacancy, id=vacancy_id)

        # Откликаться можно только одобренным резюме (оценка ИИ >= 6).
        # .first() вернёт одну запись или None, если подходящих нет
        resume = Resume.objects.filter(
            user=request.user,
            status='approved'
        ).first()

        if not resume:
            return Response(
                {'error': 'No approved resume found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # В модели стоит unique_together ['user', 'vacancy'],
        # поэтому повторный отклик на ту же вакансию база не пропустит
        application = Application.objects.create(
            user=request.user,
            vacancy=vacancy,
            resume=resume,
            cover_letter=cover_letter,
            letter_style=letter_style
        )

        # Сериализатор превращает объект модели в JSON для фронтенда
        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )


class GenerateCoverLetterView(APIView):
    """
    Генерация сопроводительного письма.  POST /api/applications/generate-letter/

    Передаёт ИИ текст резюме и описание вакансии, получает готовое письмо
    в выбранном стиле. Письмо не сохраняется — пользователь сначала
    правит его на фронтенде и только потом отправляет через ApplyView.
    """

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

            # Генерируем сопроводительное письмо через Claude
            # ИИ сопоставляет текст резюме с описанием вакансии —
            # поэтому письмо получается персональным, а не шаблонным
            ai_service = ClaudeService()
            cover_letter = ai_service.generate_cover_letter(
                resume.extracted_text,    # опыт и навыки кандидата
                vacancy.description,      # что требует работодатель
                style                     # тон письма
            )

            return Response({'letter': cover_letter})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicationListView(generics.ListAPIView):
    """Список моих откликов.  GET /api/applications/"""

    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Фильтрация по текущему пользователю — защита данных:
        без неё пользователь увидел бы отклики всех остальных.
        """
        return Application.objects.filter(user=self.request.user).order_by('-applied_at')


class ApplicationDetailView(generics.RetrieveAPIView):
    """Один отклик подробно.  GET /api/applications/<id>/"""

    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ограничение выборки своими откликами: если подставить чужой id,
        # вернётся 404, а не чужие данные
        return Application.objects.filter(user=self.request.user)
