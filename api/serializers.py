from rest_framework import serializers
from django.conf import settings
from core.domain.models import UploadedFile, EvaluationJob

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'uploaded_at']

    def validate_file(self, file):
        """Validate uploaded file size and content type."""
        max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 2 * 1024 * 1024)
        if file.size > max_size:
            raise serializers.ValidationError(f"File terlalu besar (max {max_size // 1024} KB)")

        allowed = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        content_type = getattr(file, 'content_type', None)
        if content_type and content_type not in allowed:
            raise serializers.ValidationError("Tipe file tidak diizinkan")

        return file

class EvaluationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationJob
        fields = '__all__'

class EvaluationRequestSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=255)
    cv_id = serializers.UUIDField()
    project_report_id = serializers.UUIDField()
