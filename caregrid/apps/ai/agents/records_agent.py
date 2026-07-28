import logging
import uuid
from .base import BaseAgent
from caregrid.apps.ai.services.document_processor import DocumentProcessor
from caregrid.apps.ai.models import DocumentUpload
from core.models import Patient

logger = logging.getLogger('ai')


class RecordsAgent(BaseAgent):
    """Medical Records Agent - processes and extracts data from documents."""

    agent_type = 'records'
    description = 'Document processing, data extraction, and medical records analysis'

    def __init__(self):
        super().__init__()
        self.processor = DocumentProcessor()

    def get_system_prompt(self, **kwargs) -> str:
        return self.prompt_manager.get_prompt('records', 'system')

    def process_upload(self, document_id: str, user=None) -> dict:
        """Process an uploaded document and extract structured data."""
        try:
            doc = DocumentUpload.objects.get(id=document_id)
        except DocumentUpload.DoesNotExist:
            return {'error': 'Document not found'}

        if doc.processing_status == 'completed':
            return {
                'document_id': str(doc.id),
                'status': 'already_processed',
                'extracted_data': doc.extracted_data,
            }

        doc.processing_status = 'processing'
        doc.save()

        try:
            file_path = doc.file.path
            raw_result = self.processor.process(file_path, doc.file_type)
            sanitized_content = self.processor.sanitize_content(raw_result['content'])

            extraction_prompt = self.prompt_manager.get_prompt('records', 'extract_data')
            extraction_prompt += f"\n\nDocument content:\n{sanitized_content[:8000]}"

            messages = [
                {'role': 'system', 'content': self.get_system_prompt()},
                {'role': 'user', 'content': extraction_prompt},
            ]

            response = self.llm.generate(messages, temperature=0.3)
            import json
            try:
                extracted = json.loads(response)
            except json.JSONDecodeError:
                extracted = {
                    'raw_text': response,
                    'parsing_error': 'Could not parse structured data',
                }

            from django.utils import timezone
            doc.extracted_data = extracted
            doc.processing_status = 'completed'
            doc.processed_at = timezone.now()
            doc.save()

            return {
                'document_id': str(doc.id),
                'status': 'completed',
                'extracted_data': extracted,
                'note': 'Extracted data requires doctor confirmation before saving to patient records.',
            }

        except Exception as e:
            doc.processing_status = 'failed'
            doc.processing_error = str(e)
            doc.save()
            logger.error("Document processing failed: %s", e)
            return {
                'document_id': str(doc.id),
                'status': 'failed',
                'error': str(e),
            }

    def create_upload(self, patient_id: int, file, filename: str,
                      file_type: str, file_size: int, user) -> dict:
        """Create a document upload record."""
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        doc = DocumentUpload.objects.create(
            patient=patient,
            uploaded_by=user,
            file=file,
            original_filename=filename,
            file_type=file_type,
            file_size=file_size,
        )

        return {
            'document_id': str(doc.id),
            'filename': filename,
            'status': 'pending',
            'message': 'Document uploaded. Call process endpoint to extract data.',
        }
