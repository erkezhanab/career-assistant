"""
Сериализаторы приложения resumes.

  - ResumeSerializer         — загрузка резюме и краткая информация о нём
  - ResumeAnalysisSerializer — полные результаты анализа ИИ
"""

from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    """
    Основной сериализатор резюме: приём файла и выдача краткой информации.

    Здесь же находится проверка загружаемого файла по размеру и формату.
    """

    class Meta:
        model = Resume
        # Только нужные поля: громоздкий extracted_text в список
        # резюме не попадает, чтобы ответ оставался компактным
        fields = [
            'id', 'file', 'original_filename', 'upload_date',
            'status', 'overall_score', 'analyzed_at'
        ]
        # read_only_fields — поля, которые клиент передать не может.
        # Их заполняет сервер: иначе пользователь мог бы сам
        # выставить себе статус 'approved' и оценку 10 из 10
        read_only_fields = [
            'original_filename', 'upload_date', 'status',
            'overall_score', 'analyzed_at'
        ]

    def validate_file(self, value):
        """
        Проверка загружаемого файла.

        Имя метода важно: validate_<имя поля> — DRF вызывает его
        автоматически при проверке поля file.
        """
        # Проверка размера файла
        # Ограничение защищает диск сервера от переполнения
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("Файл слишком большой. Максимум 10MB")

        # Проверка расширения
        # Вторая линия защиты (первая — валидатор в модели):
        # не даёт загрузить вместо резюме исполняемый файл
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_name = value.name.lower()
        # any() вернёт True, если имя оканчивается хотя бы на одно разрешённое расширение
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                "Неподдерживаемый формат файла. Разрешены: PDF, DOC, DOCX"
            )

        return value

    def create(self, validated_data):
        # Убедимся, что original_filename устанавливается
        # Поле read-only, поэтому заполняется здесь, на сервере,
        # из настоящего имени загруженного файла
        validated_data['original_filename'] = validated_data['file'].name
        # super() выполняет стандартное создание записи
        return super().create(validated_data)


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    """
    Полные результаты анализа резюме.

    Отдельный сериализатор нужен, чтобы тяжёлые поля (текст резюме,
    полный ответ ИИ) загружались только на странице анализа,
    а не при каждом запросе списка резюме.
    """

    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'status', 'analysis_result',
            'overall_score', 'strong_points', 'improvements',
            'recommendations', 'analyzed_at', 'extracted_text'
        ]
        # Все поля только для чтения: результаты анализа формирует ИИ,
        # изменять их через API нельзя
        read_only_fields = fields
