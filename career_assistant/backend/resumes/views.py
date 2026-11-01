"""
Представления (views) приложения resumes — загрузка и анализ резюме.

  - ResumeUploadView   — загрузка файла, извлечение текста, запуск ИИ-анализа
  - ResumeAnalysisView — результаты анализа конкретного резюме
  - ResumeDetailView   — просмотр и удаление резюме
  - UserResumesView    — список всех резюме пользователя

Главная особенность модуля — анализ ИИ запускается в фоновом потоке,
поэтому пользователь получает ответ сразу, не ожидая ответа модели.
"""

import PyPDF2            # чтение PDF-файлов
from docx import Document  # чтение DOCX-файлов
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import Resume
from .serializers import ResumeSerializer, ResumeAnalysisSerializer
from core.services.claude_service import ClaudeService
from rest_framework import serializers
import threading   # фоновое выполнение анализа
import logging     # журнал событий (вместо print — правильный способ)

# Логгер с именем текущего модуля: в логах будет видно, откуда пришло сообщение
logger = logging.getLogger(__name__)


class ResumeUploadView(generics.CreateAPIView):
    """
    Загрузка резюме.  POST /api/resumes/upload/

    Порядок действий:
      1. Проверить, что файл передан
      2. Извлечь из файла текст (PDF или DOCX)
      3. Сохранить резюме в базу вместе с текстом
      4. Запустить анализ ИИ в фоновом потоке и сразу ответить пользователю
    """

    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Парсеры для загрузки файлов: обычный JSON-парсер файлы принимать не умеет
    parser_classes = [MultiPartParser, FormParser]

    def extract_text_from_file(self, file):
        """Извлечение текста из PDF или DOCX"""
        # Текст нужен для ИИ: модель работает со строкой, а не с файлом
        text = ""

        try:
            logger.info(f"Extracting text from file: {file.name}, type: {file.content_type}")

            # Способ чтения зависит от формата файла
            if file.name.lower().endswith('.pdf'):
                reader = PyPDF2.PdfReader(file)
                # PDF читается постранично, текст страниц склеивается
                for page in reader.pages:
                    page_text = page.extract_text()
                    # Проверка нужна: со страниц-картинок (сканов) текст не извлекается
                    if page_text:
                        text += page_text + "\n"

            elif file.name.lower().endswith(('.doc', '.docx')):
                doc = Document(file)
                # DOCX читается по абзацам
                for paragraph in doc.paragraphs:
                    if paragraph.text:
                        text += paragraph.text + '\n'

            logger.info(f"Extracted {len(text)} characters from file")
            return text.strip()

        except Exception as e:
            # Файл повреждён или защищён паролем — возвращаем пустую строку,
            # а вызывающий код сообщит пользователю об ошибке
            logger.error(f"Error extracting text from {file.name}: {str(e)}")
            return ""
    
    def perform_create(self, serializer):
        file = self.request.FILES.get('file')
        if not file:
            logger.error("No file in request")
            raise serializers.ValidationError({"file": "Файл не передан"})
        
        logger.info(f"Processing file: {file.name}, size: {file.size}, type: {file.content_type}")
        
        # Извлекаем текст ДО сохранения в БД
        # Порядок важен: если текст извлечь не удалось, бесполезное резюме
        # вообще не попадёт в базу и файл не займёт место на диске
        extracted_text = self.extract_text_from_file(file)
        # Проверка на 10 символов отсекает сканы и пустые файлы:
        # анализировать такое резюме ИИ не сможет
        if not extracted_text or len(extracted_text.strip()) < 10:
            logger.error(f"Failed to extract text from file or text too short: {len(extracted_text)} chars")
            raise serializers.ValidationError({"file": "Не удалось извлечь текст из файла или файл слишком короткий"})

        # Сохраняем резюме
        # Поля user и original_filename заполняет сервер, а не клиент —
        # иначе пользователь мог бы загрузить резюме от чужого имени
        resume = serializer.save(
            user=self.request.user,
            original_filename=file.name,
            extracted_text=extracted_text  # Сохраняем текст сразу
        )

        logger.info(f"Resume created: {resume.id}, user: {resume.user.email}")

        # Запускаем анализ в фоновом режиме
        # Вызов не блокирующий: ответ уходит пользователю сразу,
        # а ИИ продолжает работать в отдельном потоке
        self.analyze_resume(resume.id)

        return resume
    
    def create(self, request, *args, **kwargs):
        """
        Обработчик POST-запроса. Переопределён, чтобы возвращать
        понятные сообщения об ошибках вместо стандартных ответов DRF.
        """
        logger.info(f"Upload request received. User: {request.user.email}")
        logger.info(f"FILES: {dict(request.FILES)}")
        logger.info(f"DATA: {dict(request.data)}")

        try:
            # Проверяем наличие файла
            # request.FILES — отдельное хранилище загруженных файлов
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
            
        # Ошибка проверки данных (не тот формат файла и т.п.) — вина клиента, код 400
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # Любая другая ошибка — вина сервера, код 500.
        # logger.exception дополнительно записывает в лог место сбоя
        except Exception as e:
            logger.exception(f"Unexpected error in resume upload: {str(e)}")
            return Response(
                # Пользователю показываем общий текст: подробности ошибки
                # могут раскрыть устройство системы
                {"error": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def analyze_resume(self, resume_id):
        """
        Анализ резюме в фоне.

        Зачем фоновый поток: ИИ отвечает 10-30 секунд. Если ждать его
        в основном потоке, браузер «висел» бы всё это время, а запрос
        мог оборваться по таймауту.

        Передаётся именно resume_id, а не объект: внутри потока запись
        читается из базы заново, чтобы данные были актуальными.
        """

        def analyze():
            """Вложенная функция — то, что будет выполняться в отдельном потоке."""
            try:
                logger.info(f"Starting analysis for resume {resume_id}")
                resume = Resume.objects.get(id=resume_id)

                # Обновляем статус на "в процессе анализа"
                # Пользователь на странице видит, что анализ идёт
                resume.status = 'pending'
                resume.save()

                ai_service = ClaudeService()

                # Получаем специализацию пользователя, если есть
                # Передаём её ИИ, чтобы резюме оценивалось под конкретную профессию.
                # hasattr защищает от ошибки, если поля нет
                specialization = None
                if hasattr(resume.user, 'specialization') and resume.user.specialization:
                    specialization = resume.user.specialization

                # Основной вызов ИИ
                analysis = ai_service.analyze_resume(
                    resume.extracted_text,
                    specialization
                )

                # Обновляем поля резюме
                # Полный ответ сохраняем целиком — на случай новых полей в будущем
                resume.analysis_result = analysis
                # .get() с запасным значением: если ИИ не вернул оценку, ставим 5.0
                resume.overall_score = analysis.get('overall_score', 5.0)

                # Преобразуем списки в строки
                # ИИ возвращает списки, а в модели эти поля текстовые,
                # поэтому элементы склеиваются через перенос строки
                strong_points = analysis.get('strong_points', [])
                improvements = analysis.get('improvements', [])
                recommendations = analysis.get('additions', [])

                # isinstance-проверки: если ИИ вернул строку вместо списка,
                # код не упадёт, а просто сохранит её как есть
                resume.strong_points = '\n'.join(strong_points) if isinstance(strong_points, list) else str(strong_points)
                resume.improvements = '\n'.join(improvements) if isinstance(improvements, list) else str(improvements)
                resume.recommendations = '\n'.join(recommendations) if isinstance(recommendations, list) else str(recommendations)

                resume.analyzed_at = timezone.now()

                # Определяем статус на основе оценки
                # Порог 6 из 10: только одобренные резюме допускаются
                # к отправке откликов и генерации писем
                if resume.overall_score >= 6.0:
                    resume.status = 'approved'
                else:
                    resume.status = 'rejected'

                resume.save()
                logger.info(f"Analysis completed for resume {resume_id}, score: {resume.overall_score}, status: {resume.status}")
                
            # Резюме удалили, пока шёл анализ — просто выходим
            except Resume.DoesNotExist:
                logger.error(f"Resume {resume_id} not found")
            except Exception as e:
                # ИИ недоступен или вернул некорректные данные.
                # Ошибку нельзя показать пользователю напрямую (мы в фоне),
                # поэтому помечаем резюме статусом 'failed' — он виден в интерфейсе
                logger.error(f"Error analyzing resume {resume_id}: {str(e)}")
                # Обновляем статус как "failed"
                try:
                    resume = Resume.objects.get(id=resume_id)
                    resume.status = 'failed'
                    resume.save()
                    logger.info(f"Resume {resume_id} status set to 'failed'")
                except:
                    # Не удалось даже записать статус — поток молча завершается,
                    # чтобы необработанное исключение не «уронило» его
                    pass

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=analyze)
        # daemon=True — поток не мешает серверу завершить работу:
        # при остановке Django такие потоки закрываются автоматически
        thread.daemon = True
        thread.start()
        logger.info(f"Analysis thread started for resume {resume_id}")


class ResumeAnalysisView(generics.RetrieveAPIView):
    """
    Результаты анализа резюме.  GET /api/resumes/<id>/analysis/

    Фронтенд периодически обращается сюда, пока статус 'pending',
    чтобы показать результат, как только фоновый анализ закончится.
    """

    serializer_class = ResumeAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # self.kwargs['pk'] — id из адреса запроса
        resume_id = self.kwargs['pk']
        try:
            # Условие user=... обязательно: без него можно было бы
            # посмотреть анализ чужого резюме, подставив его id
            return Resume.objects.get(id=resume_id, user=self.request.user)
        except Resume.DoesNotExist:
            raise serializers.ValidationError({"error": "Резюме не найдено"})


class ResumeDetailView(generics.RetrieveDestroyAPIView):
    """
    Просмотр и удаление резюме.  GET/DELETE /api/resumes/<id>/

    RetrieveDestroyAPIView = чтение + удаление.
    При удалении срабатывает метод Resume.delete(), который
    убирает и сам файл с диска.
    """

    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ограничение своими резюме — защита от удаления чужих файлов
        return Resume.objects.filter(user=self.request.user)


class UserResumesView(generics.ListAPIView):
    """Список всех моих резюме.  GET /api/resumes/my/"""

    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Сначала самые свежие (минус перед полем = сортировка по убыванию)
        return Resume.objects.filter(user=self.request.user).order_by('-upload_date')