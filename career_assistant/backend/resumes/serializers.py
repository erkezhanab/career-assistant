from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            'id', 'file', 'original_filename', 'upload_date', 
            'status', 'overall_score', 'analyzed_at'
        ]
        read_only_fields = [
            'original_filename', 'upload_date', 'status', 
            'overall_score', 'analyzed_at'
        ]
    
    def validate_file(self, value):
        # Проверка размера файла
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("Файл слишком большой. Максимум 10MB")
        
        # Проверка расширения
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_name = value.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                "Неподдерживаемый формат файла. Разрешены: PDF, DOC, DOCX"
            )
        
        return value
    
    def create(self, validated_data):
        # Убедимся, что original_filename устанавливается
        validated_data['original_filename'] = validated_data['file'].name
        return super().create(validated_data)


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'status', 'analysis_result',
            'overall_score', 'strong_points', 'improvements', 
            'recommendations', 'analyzed_at', 'extracted_text'
        ]
        read_only_fields = fields