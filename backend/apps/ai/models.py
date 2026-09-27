import uuid
from django.db import models
from django.conf import settings


class AuditTrail(models.Model):
    ACTION_TYPES = [
        ('summary', 'AI Summary Generated'),
        ('diagnosis_suggestion', 'AI Diagnosis Suggested'),
        ('test_recommendation', 'AI Test Recommended'),
        ('record_extraction', 'Medical Record Extracted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_audit_trails'
    )
    patient = models.ForeignKey(
        'core.Patient', on_delete=models.SET_NULL, null=True, blank=True
    )
    conversation = models.ForeignKey(
        'Conversation', on_delete=models.SET_NULL, null=True, blank=True
    )
    document = models.ForeignKey(
        'UploadedDocument', on_delete=models.SET_NULL, null=True, blank=True
    )
    ai_model = models.CharField(max_length=255, blank=True, default='')
    input_summary = models.TextField(blank=True, default='')
    output_summary = models.TextField(blank=True, default='')
    confidence_score = models.FloatField(null=True, blank=True)
    blockchain_hash = models.CharField(max_length=66, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type']),
            models.Index(fields=['doctor', 'created_at']),
            models.Index(fields=['patient', 'created_at']),
        ]

    def __str__(self):
        return f"{self.action_type} by {self.doctor} at {self.created_at.isoformat()}"


class MedicalRecord(models.Model):
    RECORD_TYPES = [
        ('diagnosis', 'Diagnosis'),
        ('lab_result', 'Lab Result'),
        ('prescription', 'Prescription'),
        ('visit_note', 'Visit Note'),
        ('discharge', 'Discharge Summary'),
        ('referral', 'Referral'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'core.Patient', on_delete=models.CASCADE, related_name='medical_records'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medical_records'
    )
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    structured_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'record_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.record_type} for {self.patient} on {self.created_at.date()}"


class Conversation(models.Model):
    AGENT_TYPES = [
        ('doctor', 'Doctor Assistant'),
        ('medical_records', 'Medical Records Agent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_conversations'
    )
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    title = models.CharField(max_length=255, blank=True, default='')
    doctor = models.ForeignKey(
        'core.Doctor', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_conversations'
    )
    patient = models.ForeignKey(
        'core.Patient', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_conversations'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'agent_type']),
            models.Index(fields=['patient']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return f"{self.agent_type} conversation {self.id}"


class Message(models.Model):
    ROLES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLES)
    content = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role} in {self.conversation_id}"


class UploadedDocument(models.Model):
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('txt', 'Text'),
    ]
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'core.Patient', on_delete=models.CASCADE, related_name='ai_uploaded_documents'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_uploads'
    )
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.PositiveIntegerField()
    file_path = models.CharField(max_length=512, blank=True, default='')
    processing_status = models.CharField(
        max_length=20, choices=PROCESSING_STATUS, default='pending'
    )
    extracted_text = models.TextField(blank=True, default='')
    processing_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.processing_status})"


class EmbeddingMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        UploadedDocument, on_delete=models.CASCADE, related_name='embeddings',
        null=True, blank=True
    )
    source_type = models.CharField(max_length=50, default='document')
    source_id = models.CharField(max_length=255, blank=True, default='')
    chunk_index = models.PositiveIntegerField(default=0)
    chunk_text = models.TextField()
    embedding_model = models.CharField(max_length=255, blank=True, default='')
    vector_id = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['vector_id']),
            models.Index(fields=['source_type', 'source_id']),
        ]

    def __str__(self):
        return f"Embedding {self.vector_id} for {self.source_type}"


class AISummary(models.Model):
    SUMMARY_TYPES = [
        ('patient_history', 'Patient History Summary'),
        ('appointments', 'Appointments Summary'),
        ('prescriptions', 'Prescriptions Summary'),
        ('documents', 'Documents Summary'),
        ('findings', 'Abnormal Findings'),
        ('diagnoses', 'Suggested Diagnoses'),
        ('tests', 'Suggested Tests'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'core.Patient', on_delete=models.CASCADE, related_name='ai_summaries'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_summaries_created'
    )
    summary_type = models.CharField(max_length=30, choices=SUMMARY_TYPES)
    content = models.TextField()
    source_conversation = models.ForeignKey(
        Conversation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='summaries'
    )
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_summaries_approved'
    )
    blockchain_hash = models.CharField(max_length=66, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'summary_type']),
            models.Index(fields=['approved']),
        ]

    def __str__(self):
        return f"{self.summary_type} summary for {self.patient}"
