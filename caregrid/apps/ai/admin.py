from django.contrib import admin
from .models import (
    Conversation,
    Message,
    AISummary,
    DocumentUpload,
    KnowledgeDocument,
)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('role', 'content', 'tokens_used', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'agent_type', 'patient_context', 'is_active', 'created_at')
    list_filter = ('agent_type', 'is_active')
    search_fields = ('user__username',)
    inlines = [MessageInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'tokens_used', 'created_at')
    list_filter = ('role',)
    readonly_fields = ('created_at',)


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'summary_type', 'approved', 'doctor', 'created_at')
    list_filter = ('summary_type', 'approved')
    search_fields = ('patient__name',)
    readonly_fields = ('created_at',)


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'patient', 'file_type', 'processing_status', 'created_at')
    list_filter = ('file_type', 'processing_status')
    search_fields = ('original_filename',)
    readonly_fields = ('created_at', 'processed_at')


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('title',)
    readonly_fields = ('created_at', 'updated_at')
