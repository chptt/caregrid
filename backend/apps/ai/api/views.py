import json
import logging
import os
import uuid

from django.conf import settings
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from backend.apps.ai.agents.doctor.agent import DoctorAgent
from backend.apps.ai.agents.medical_records.agent import MedicalRecordsAgent
from backend.apps.ai.models import Conversation, Message, UploadedDocument, EmbeddingMetadata
from backend.apps.ai.serializers.chat import ChatRequestSerializer
from backend.apps.ai.serializers.document import (
    UploadDocumentSerializer, DocumentResponseSerializer, DocumentListSerializer,
)
from backend.apps.ai.serializers.conversation import (
    ConversationListSerializer, ConversationDetailSerializer, MessageSerializer,
)
from backend.apps.ai.document_processing.extractor import extract, validate_file
from backend.apps.ai.document_processing.cleaner import sanitize
from backend.apps.ai.document_processing.chunker import TextChunker
from backend.apps.ai.rag.pipeline import RAGPipeline
from backend.apps.ai.embeddings.openai import OpenAIEmbeddingProvider
from backend.apps.ai.core.exceptions import DocumentProcessingError
from core.response_helpers import (
    success_response, error_response, created_response,
    not_found_response, forbidden_response,
)

logger = logging.getLogger('ai')


class DoctorChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        patient = None
        if serializer.validated_data.get('patient_id'):
            from core.models import Patient
            try:
                patient = Patient.objects.get(id=serializer.validated_data['patient_id'])
            except Patient.DoesNotExist:
                return not_found_response('Patient not found')

        agent = DoctorAgent()
        result = agent.chat(
            user_message=serializer.validated_data['message'],
            conversation_id=str(serializer.validated_data.get('conversation_id', '')) or None,
            user=request.user,
            patient=patient,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class MedicalRecordsChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        action = request.data.get('action', 'extract')
        document_text = request.data.get('document_text', '')
        filename = request.data.get('filename', '')
        conversation_id = request.data.get('conversation_id')

        if not document_text:
            return error_response('document_text is required')

        patient = None
        if request.data.get('patient_id'):
            from core.models import Patient
            try:
                patient = Patient.objects.get(id=request.data['patient_id'])
            except Patient.DoesNotExist:
                return not_found_response('Patient not found')

        agent = MedicalRecordsAgent()

        if action == 'summarize':
            result = agent.summarize(
                document_text=document_text, filename=filename,
                user=request.user, patient=patient,
                conversation_id=conversation_id,
            )
        elif action == 'analyze':
            result = agent.analyze(
                document_text=document_text, filename=filename,
                user=request.user, patient=patient,
                conversation_id=conversation_id,
            )
        else:
            result = agent.extract(
                document_text=document_text, filename=filename,
                user=request.user, patient=patient,
                conversation_id=conversation_id,
            )

        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UploadDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        from core.models import Patient
        try:
            patient = Patient.objects.get(id=serializer.validated_data['patient_id'])
        except Patient.DoesNotExist:
            return not_found_response('Patient not found')

        upload_file = serializer.validated_data['file']
        try:
            validate_file(upload_file.name, upload_file.size)
        except ValueError as e:
            return error_response(str(e))

        ext = upload_file.name.rsplit('.', 1)[-1].lower()

        upload_dir = settings.BASE_DIR / 'ai_uploads' / str(patient.id)
        os.makedirs(upload_dir, exist_ok=True)

        safe_filename = f"{uuid.uuid4()}.{ext}"
        file_path = str(upload_dir / safe_filename)

        with open(file_path, 'wb+') as dest:
            for chunk in upload_file.chunks():
                dest.write(chunk)

        doc = UploadedDocument.objects.create(
            patient=patient,
            uploaded_by=request.user,
            original_filename=upload_file.name,
            file_type=ext,
            file_size=upload_file.size,
            file_path=file_path,
            processing_status='processing',
        )

        try:
            raw_text = extract(file_path, ext)
            cleaned = sanitize(raw_text)

            chunker = TextChunker()
            chunks = chunker.chunk(cleaned)

            embedding_provider = OpenAIEmbeddingProvider()
            rag = RAGPipeline(embedding_provider=embedding_provider)
            vector_ids = rag.ingest(
                text=cleaned,
                source_type='document',
                source_id=str(doc.id),
                metadata={
                    'title': upload_file.name,
                    'patient_id': str(patient.id),
                },
            )

            for chunk, vid in zip(chunks, vector_ids):
                EmbeddingMetadata.objects.create(
                    document=doc,
                    source_type='document',
                    source_id=str(doc.id),
                    chunk_index=chunk.index,
                    chunk_text=chunk.text,
                    embedding_model=embedding_provider.model,
                    vector_id=vid,
                )

            doc.extracted_text = cleaned
            doc.processing_status = 'completed'
            doc.save()

        except Exception as e:
            doc.processing_status = 'failed'
            doc.processing_error = str(e)
            doc.save()
            return error_response(f"Document processing failed: {e}", status_code=500)

        return created_response(data={
            'document_id': str(doc.id),
            'original_filename': doc.original_filename,
            'file_type': doc.file_type,
            'file_size': doc.file_size,
            'processing_status': doc.processing_status,
        })


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        documents = UploadedDocument.objects.filter(uploaded_by=request.user)
        if patient_id:
            documents = documents.filter(patient_id=patient_id)
        documents = documents.order_by('-created_at')
        serializer = DocumentListSerializer(documents, many=True)
        return success_response(data={'documents': serializer.data})


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        try:
            doc = UploadedDocument.objects.get(id=document_id)
        except UploadedDocument.DoesNotExist:
            return not_found_response('Document not found')

        return success_response(data={
            'document_id': str(doc.id),
            'original_filename': doc.original_filename,
            'file_type': doc.file_type,
            'file_size': doc.file_size,
            'processing_status': doc.processing_status,
            'extracted_text': doc.extracted_text,
            'created_at': doc.created_at.isoformat(),
        })


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get('search', '')
        agent_type = request.query_params.get('agent_type', '')
        page = int(request.query_params.get('page', '1'))
        page_size = int(request.query_params.get('page_size', '20'))

        conversations = Conversation.objects.filter(user=request.user)

        if search:
            conversations = conversations.filter(
                Q(title__icontains=search) | Q(patient__name__icontains=search)
            )
        if agent_type:
            conversations = conversations.filter(agent_type=agent_type)

        conversations = conversations.annotate(
            message_count=Count('messages')
        ).order_by('-created_at')

        total = conversations.count()
        start = (page - 1) * page_size
        end = start + page_size
        page_convs = conversations[start:end]

        serializer = ConversationListSerializer(page_convs, many=True)
        return success_response(data={
            'conversations': serializer.data,
            'total': total,
            'page': page,
            'page_size': page_size,
        })


class ConversationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return not_found_response('Conversation not found')

        if conversation.user != request.user:
            return forbidden_response('Access denied')

        messages = conversation.messages.all().order_by('created_at')
        msg_data = MessageSerializer(messages, many=True).data
        serializer = ConversationDetailSerializer(conversation)
        data = serializer.data
        data['messages'] = msg_data
        return success_response(data=data)

    def delete(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return not_found_response('Conversation not found')

        if conversation.user != request.user:
            return forbidden_response('Access denied')

        conversation.is_active = False
        conversation.save(update_fields=['is_active'])
        return success_response(message='Conversation deleted')
