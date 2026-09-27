from django.contrib import admin
from .models import (
    Conversation,
    Message,
    UploadedDocument,
    EmbeddingMetadata,
    AISummary,
    MedicalRecord,
)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('role', 'content', 'tokens_used', 'created_at')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'record_type', 'title', 'created_at')
    list_filter = ('record_type',)
    search_fields = ('patient__name', 'title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'agent_type', 'doctor', 'patient', 'is_active', 'created_at')
    list_filter = ('agent_type', 'is_active')
    search_fields = ('user__username',)
    inlines = [MessageInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'tokens_used', 'created_at')
    list_filter = ('role',)
    readonly_fields = ('created_at',)


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'patient', 'file_type', 'processing_status', 'created_at')
    list_filter = ('file_type', 'processing_status')
    search_fields = ('original_filename',)
    readonly_fields = ('created_at', 'processed_at')


@admin.register(EmbeddingMetadata)
class EmbeddingMetadataAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'source_type', 'chunk_index', 'embedding_model', 'created_at')
    list_filter = ('source_type',)
    readonly_fields = ('created_at',)


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'summary_type', 'approved', 'doctor', 'created_at')
    list_filter = ('summary_type', 'approved')
    search_fields = ('patient__name',)
    readonly_fields = ('created_at',)
