from rest_framework import serializers


class UploadDocumentSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    file = serializers.FileField()


class DocumentResponseSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    original_filename = serializers.CharField()
    file_type = serializers.CharField()
    file_size = serializers.IntegerField()
    processing_status = serializers.CharField()
    extracted_text = serializers.CharField(required=False)
    created_at = serializers.DateTimeField(required=False)


class DocumentListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    original_filename = serializers.CharField()
    file_type = serializers.CharField()
    file_size = serializers.IntegerField()
    processing_status = serializers.CharField()
    created_at = serializers.DateTimeField()
