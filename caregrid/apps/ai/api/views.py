import os
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from caregrid.apps.ai.agents.doctor_agent import DoctorAssistant
from caregrid.apps.ai.agents.patient_agent import PatientAssistant
from caregrid.apps.ai.agents.records_agent import RecordsAgent
from caregrid.apps.ai.services.document_processor import DocumentProcessor
from caregrid.apps.ai.rag.retriever import Retriever
from caregrid.apps.ai.rag.ingestor import KnowledgeIngestor
from caregrid.apps.ai.models import Conversation, AISummary, DocumentUpload, KnowledgeDocument
from core.response_helpers import error_response, success_response, created_response, not_found_response
from .serializers import (
    ChatRequestSerializer, SummarizeHistorySerializer, VisitSummarySerializer,
    UploadDocumentSerializer, ProcessDocumentSerializer, KnowledgeDocumentSerializer,
    ExplainDiagnosisSerializer, MedicationInfoSerializer, GeneralHealthSerializer,
)
from .permissions import IsDoctorOrAdmin, IsPatient, IsDoctorAdminOrNurse, IsKnowledgeAdmin

logger = logging.getLogger('ai')


class DoctorChatView(APIView):
    permission_classes = [IsDoctorOrAdmin]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = DoctorAssistant()
        patient_context = None
        if serializer.validated_data.get('patient_id'):
            from core.models import Patient
            try:
                patient_context = Patient.objects.get(id=serializer.validated_data['patient_id'])
            except Patient.DoesNotExist:
                return not_found_response('Patient not found')

        result = agent.chat(
            user_message=serializer.validated_data['message'],
            conversation_id=str(serializer.validated_data.get('conversation_id', '')) or None,
            user=request.user,
            patient_context=patient_context,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class DoctorSummarizeHistoryView(APIView):
    permission_classes = [IsDoctorOrAdmin]

    def post(self, request):
        serializer = SummarizeHistorySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = DoctorAssistant()
        result = agent.summarize_patient_history(
            patient_id=serializer.validated_data['patient_id'],
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class DoctorVisitSummaryView(APIView):
    permission_classes = [IsDoctorOrAdmin]

    def post(self, request):
        serializer = VisitSummarySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = DoctorAssistant()
        result = agent.generate_visit_summary(
            patient_id=serializer.validated_data['patient_id'],
            visit_notes=serializer.validated_data['visit_notes'],
            doctor_notes=serializer.validated_data.get('doctor_notes', ''),
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class PatientChatView(APIView):
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = PatientAssistant()
        result = agent.chat(
            user_message=serializer.validated_data['message'],
            conversation_id=str(serializer.validated_data.get('conversation_id', '')) or None,
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class PatientExplainDiagnosisView(APIView):
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = ExplainDiagnosisSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = PatientAssistant()
        result = agent.explain_diagnosis(
            diagnosis_text=serializer.validated_data['diagnosis_text'],
            conversation_id=str(serializer.validated_data.get('conversation_id', '')) or None,
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class PatientMedicationInfoView(APIView):
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = MedicationInfoSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = PatientAssistant()
        result = agent.medication_info(
            medication_name=serializer.validated_data['medication_name'],
            dosage=serializer.validated_data.get('dosage', ''),
            conversation_id=str(serializer.validated_data.get('conversation_id', '')) or None,
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class PatientGeneralHealthView(APIView):
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = GeneralHealthSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = PatientAssistant()
        result = agent.general_health_query(
            question=serializer.validated_data['question'],
            conversation_id=str(serializer.validated_data.get('conversation_id', '')) or None,
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'], status_code=500)
        return success_response(data=result)


class UploadDocumentView(APIView):
    permission_classes = [IsDoctorAdminOrNurse]

    def post(self, request):
        serializer = UploadDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        upload_file = serializer.validated_data['file']
        file_size = upload_file.size
        max_size = DocumentProcessor.MAX_FILE_SIZE

        if file_size > max_size:
            return error_response(
                f'File too large. Maximum size is {max_size // (1024 * 1024)}MB.'
            )

        filename = upload_file.name
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in DocumentProcessor.ALLOWED_EXTENSIONS:
            return error_response(
                f'Unsupported file type. Allowed: {", ".join(DocumentProcessor.ALLOWED_EXTENSIONS)}'
            )

        agent = RecordsAgent()
        result = agent.create_upload(
            patient_id=serializer.validated_data['patient_id'],
            file=upload_file,
            filename=filename,
            file_type=ext,
            file_size=file_size,
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'])
        return created_response(data=result)


class ProcessDocumentView(APIView):
    permission_classes = [IsDoctorAdminOrNurse]

    def post(self, request):
        serializer = ProcessDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        agent = RecordsAgent()
        result = agent.process_upload(
            document_id=str(serializer.validated_data['document_id']),
            user=request.user,
        )
        if 'error' in result:
            return error_response(result['error'])
        return success_response(data=result)


class ApproveSummaryView(APIView):
    permission_classes = [IsDoctorOrAdmin]

    def post(self, request, summary_id):
        try:
            summary = AISummary.objects.get(id=summary_id)
        except AISummary.DoesNotExist:
            return not_found_response('Summary not found')

        summary.approved = True
        summary.approved_by = request.user
        summary.save()

        return success_response(data={
            'summary_id': str(summary.id),
            'approved': True,
            'approved_by': request.user.username,
        })


class ConversationHistoryView(APIView):
    permission_classes = []

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return not_found_response('Conversation not found')

        if conversation.user != request.user and request.user.role != 'admin':
            return error_response('Access denied', status_code=403)

        messages = conversation.messages.all().values('role', 'content', 'created_at', 'tokens_used')
        return success_response(data={
            'conversation_id': str(conversation.id),
            'agent_type': conversation.agent_type,
            'messages': list(messages),
        })


class RAGSearchView(APIView):
    permission_classes = [IsDoctorOrAdmin]

    def post(self, request):
        query = request.data.get('query', '')
        if not query:
            return error_response('Query is required')

        category = request.data.get('category')
        top_k = request.data.get('top_k', 5)

        retriever = Retriever()
        results = retriever.retrieve(query, top_k=top_k, category=category)
        return success_response(data={'results': results, 'query': query})


class KnowledgeListView(APIView):
    permission_classes = [IsKnowledgeAdmin]

    def get(self, request):
        docs = KnowledgeDocument.objects.filter(is_active=True)
        data = [{
            'id': str(d.id),
            'title': d.title,
            'category': d.category,
            'created_at': str(d.created_at),
        } for d in docs]
        return success_response(data={'documents': data})

    def post(self, request):
        serializer = KnowledgeDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response('Invalid request', details=serializer.errors)

        ingestor = KnowledgeIngestor()
        doc = ingestor.ingest_document(
            title=serializer.validated_data['title'],
            content=serializer.validated_data['content'],
            category=serializer.validated_data['category'],
            created_by=request.user,
        )
        return created_response(data={
            'id': str(doc.id),
            'title': doc.title,
            'category': doc.category,
        })
