import uuid
from django.db import models
from django.conf import settings


class Conversation(models.Model):
    AGENT_TYPES = [
        ('doctor', 'Doctor Assistant'),
        ('patient', 'Patient Assistant'),
        ('records', 'Medical Records Agent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
    )
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    patient_context = models.ForeignKey(
        'core.Patient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agent_type} conversation {self.id} by {self.user.username}"


class Message(models.Model):
    ROLES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
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


class AISummary(models.Model):
    SUMMARY_TYPES = [
        ('history', 'Patient History Summary'),
        ('visit', 'Visit Summary'),
        ('lab', 'Lab Results Summary'),
        ('prescription', 'Prescription Summary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'core.Patient',
        on_delete=models.CASCADE,
        related_name='ai_summaries',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_summaries_created',
    )
    summary_type = models.CharField(max_length=20, choices=SUMMARY_TYPES)
    content = models.TextField()
    source_conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='summaries',
    )
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_summaries_approved',
    )
    blockchain_hash = models.CharField(max_length=66, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.summary_type} summary for {self.patient}"


class DocumentUpload(models.Model):
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('txt', 'Text'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'core.Patient',
        on_delete=models.CASCADE,
        related_name='ai_documents',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_uploads',
    )
    file = models.FileField(upload_to='ai_uploads/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.PositiveIntegerField()
    processing_status = models.CharField(
        max_length=20, choices=PROCESSING_STATUS, default='pending'
    )
    extracted_data = models.JSONField(null=True, blank=True)
    processing_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.processing_status})"


class KnowledgeDocument(models.Model):
    CATEGORIES = [
        ('policy', 'Hospital Policy'),
        ('guideline', 'Treatment Guideline'),
        ('protocol', 'Clinical Protocol'),
        ('drug_info', 'Drug Information'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    content = models.TextField()
    embedding_id = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knowledge_docs_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.category})"
