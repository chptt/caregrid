import json
import logging
from django.utils import timezone

from backend.apps.ai.models import AuditTrail
from backend.apps.ai.services.blockchain import AISummaryBlockchainService

logger = logging.getLogger('ai')


class AuditService:
    @staticmethod
    def _create_entry(action_type, doctor, patient, conversation_id=None,
                      document_id=None, input_text='', output_text='',
                      ai_model='', confidence_score=None):
        from backend.apps.ai.models import Conversation, UploadedDocument
        conversation = None
        document = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except (Conversation.DoesNotExist, ValueError):
                pass
        if document_id:
            try:
                document = UploadedDocument.objects.get(id=document_id)
            except (UploadedDocument.DoesNotExist, ValueError):
                pass

        content_hash = AISummaryBlockchainService.hash_summary(output_text)

        return AuditTrail.objects.create(
            action_type=action_type,
            doctor=doctor,
            patient=patient,
            conversation=conversation,
            document=document,
            ai_model=ai_model or '',
            input_summary=input_text[:5000],
            output_summary=output_text[:5000],
            confidence_score=confidence_score,
            blockchain_hash=content_hash,
        )

    @staticmethod
    def log_summary(doctor, patient, conversation_id=None,
                    input_text='', output_text='', ai_model=''):
        return AuditService._create_entry(
            'summary', doctor, patient, conversation_id,
            input_text=input_text, output_text=output_text, ai_model=ai_model,
        )

    @staticmethod
    def log_diagnosis_suggestion(doctor, patient, conversation_id=None,
                                 input_text='', output_text='', ai_model=''):
        return AuditService._create_entry(
            'diagnosis_suggestion', doctor, patient, conversation_id,
            input_text=input_text, output_text=output_text, ai_model=ai_model,
        )

    @staticmethod
    def log_test_recommendation(doctor, patient, conversation_id=None,
                                input_text='', output_text='', ai_model=''):
        return AuditService._create_entry(
            'test_recommendation', doctor, patient, conversation_id,
            input_text=input_text, output_text=output_text, ai_model=ai_model,
        )

    @staticmethod
    def log_extraction(doctor, patient, conversation_id=None,
                       input_text='', output_text='', ai_model=''):
        return AuditService._create_entry(
            'record_extraction', doctor, patient, conversation_id,
            input_text=input_text, output_text=output_text, ai_model=ai_model,
        )
