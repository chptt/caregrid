from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=10000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    patient_id = serializers.IntegerField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField()
    response = serializers.CharField()
    agent_type = serializers.CharField()
    tokens_used = serializers.IntegerField()


class SummarizeHistorySerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()


class VisitSummarySerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    visit_notes = serializers.CharField(max_length=10000)
    doctor_notes = serializers.CharField(max_length=5000, required=False, allow_blank=True)


class UploadDocumentSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    file = serializers.FileField()


class ProcessDocumentSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()


class ApproveSummarySerializer(serializers.Serializer):
    summary_id = serializers.UUIDField()


class KnowledgeDocumentSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    category = serializers.ChoiceField(
        choices=[('policy', 'Policy'), ('guideline', 'Guideline'),
                 ('protocol', 'Protocol'), ('drug_info', 'Drug Info')]
    )
    content = serializers.CharField(max_length=100000)


class ConversationHistorySerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField()


class ExplainDiagnosisSerializer(serializers.Serializer):
    diagnosis_text = serializers.CharField(max_length=10000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    patient_id = serializers.IntegerField(required=False, allow_null=True)


class MedicationInfoSerializer(serializers.Serializer):
    medication_name = serializers.CharField(max_length=200)
    dosage = serializers.CharField(max_length=100, required=False, allow_blank=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    patient_id = serializers.IntegerField(required=False, allow_null=True)


class GeneralHealthSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=5000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    patient_id = serializers.IntegerField(required=False, allow_null=True)
