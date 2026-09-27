import logging
from typing import Any

from backend.apps.ai.agents.base.agent import BaseAgent
from backend.apps.ai.rag.pipeline import RAGPipeline
from backend.apps.ai.core.registry import AgentRegistry
from backend.apps.ai.models import UploadedDocument, AISummary, MedicalRecord
from backend.apps.ai.providers.base import BaseLLMProvider
from backend.apps.ai.services.audit import AuditService
from core.models import Patient, Appointment as PatientAppointment

logger = logging.getLogger('ai')

DISCLAIMER = "AI Suggestion — Requires Doctor Verification"


class DoctorAgent(BaseAgent):
    agent_type = 'doctor'
    description = 'Clinical decision support with patient data analysis'

    def __init__(self, llm_provider: BaseLLMProvider | None = None):
        super().__init__(llm_provider)
        self.rag = RAGPipeline()

    def get_system_prompt(self, **kwargs) -> str:
        base = self.prompt_manager.get('doctor', 'system')
        patient = kwargs.get('patient')
        if patient:
            base += f"\n\nCurrent Patient: {self._format_patient_context(patient)}"
        rag_context = kwargs.get('rag_context', '')
        if rag_context:
            base += f"\n\nRelevant Context:\n{rag_context}"
        return base

    def chat(self, user_message: str, **kwargs) -> dict[str, Any]:
        rag_context = self.rag.build_context(user_message, top_k=3)
        kwargs['rag_context'] = rag_context
        result = super().chat(user_message, **kwargs)
        if DISCLAIMER not in result.get('response', ''):
            result['response'] = result['response'].rstrip() + f"\n\n{DISCLAIMER}"
        result['explanation'] = self._build_explanation_panel(result.get('response', ''))
        return result

    def summarize_patient(self, patient_id: int, user=None,
                          conversation_id: str | None = None) -> dict[str, Any]:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        prompt = self.prompt_manager.get('doctor', 'summarize_patient')
        prompt += f"\n\nPatient: {patient.name}, DOB: {patient.date_of_birth}, Gender: {patient.gender}"

        records = MedicalRecord.objects.filter(patient=patient).values('record_type', 'title', 'content')[:20]
        if records:
            prompt += f"\n\nMedical Records:\n{list(records)}"

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )
        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_summary(
                doctor=user, patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=prompt[:2000], output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )
        return result

    def summarize_appointments(self, patient_id: int, user=None,
                               conversation_id: str | None = None) -> dict[str, Any]:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        appointments = PatientAppointment.objects.filter(patient=patient).order_by('-date')[:20]
        appt_data = [{'doctor': a.doctor.name, 'date': str(a.date), 'branch': str(a.branch)} for a in appointments]

        prompt = self.prompt_manager.get('doctor', 'summarize_appointments')
        prompt += f"\n\nAppointments ({len(appt_data)}):\n{appt_data}"

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )
        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_summary(
                doctor=user, patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=prompt[:2000], output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )
        return result

    def summarize_prescriptions(self, patient_id: int, user=None,
                                conversation_id: str | None = None) -> dict[str, Any]:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        records = MedicalRecord.objects.filter(patient=patient, record_type='prescription').values('title', 'content', 'created_at')[:20]

        prompt = self.prompt_manager.get('doctor', 'summarize_prescriptions')
        if records:
            prompt += f"\n\nPrescription Records ({len(records)}):\n{list(records)}"
        else:
            prompt += "\n\nNo prescription records found."

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )
        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_summary(
                doctor=user, patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=prompt[:2000], output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )
        return result

    def summarize_documents(self, patient_id: int, user=None,
                            conversation_id: str | None = None) -> dict[str, Any]:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        docs = UploadedDocument.objects.filter(
            patient=patient, processing_status='completed'
        ).values('original_filename', 'file_type', 'extracted_text')[:20]

        prompt = self.prompt_manager.get('doctor', 'summarize_documents')
        if docs:
            prompt += f"\n\nUploaded Documents ({len(docs)}):\n{list(docs)}"
        else:
            prompt += "\n\nNo processed documents found."

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )
        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_summary(
                doctor=user, patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=prompt[:2000], output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )
        return result

    def highlight_findings(self, patient_id: int, user=None,
                           conversation_id: str | None = None) -> dict[str, Any]:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        appointments = PatientAppointment.objects.filter(patient=patient).order_by('-date')[:10]
        records = MedicalRecord.objects.filter(patient=patient)[:10]
        docs = UploadedDocument.objects.filter(patient=patient, processing_status='completed')[:5]

        prompt = self.prompt_manager.get('doctor', 'highlight_findings')
        prompt += f"\n\nPatient: {patient.name}, DOB: {patient.date_of_birth}, Gender: {patient.gender}"
        prompt += f"\nRecent Appointments: {[str(a.date) for a in appointments]}"
        prompt += f"\nMedical Records: {[r.title for r in records]}"
        prompt += f"\nUploaded Docs: {[d.original_filename for d in docs]}"

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )
        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_summary(
                doctor=user, patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=prompt[:2000], output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )
        return result

    def suggest_diagnoses(self, patient_id: int, user=None,
                          conversation_id: str | None = None) -> dict[str, Any]:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        records = MedicalRecord.objects.filter(patient=patient)[:15]
        appointments = PatientAppointment.objects.filter(patient=patient).order_by('-date')[:10]

        prompt = self.prompt_manager.get('doctor', 'suggest_diagnoses')
        prompt += f"\n\nPatient: {patient.name}, DOB: {patient.date_of_birth}, Gender: {patient.gender}"
        prompt += f"\nMedical Records: {[{'type': r.record_type, 'title': r.title} for r in records]}"
        prompt += f"\nRecent Visits: {[str(a.date) + ' with ' + a.doctor.name for a in appointments]}"

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )
        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_diagnosis_suggestion(
                doctor=user, patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=prompt[:2000], output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )
        return result

    def suggest_tests(self, patient_id: int, user=None,
                      conversation_id: str | None = None) -> dict[str, Any]:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        records = MedicalRecord.objects.filter(patient=patient)[:15]

        prompt = self.prompt_manager.get('doctor', 'suggest_tests')
        prompt += f"\n\nPatient: {patient.name}, DOB: {patient.date_of_birth}, Gender: {patient.gender}"
        if records:
            prompt += f"\nMedical Records: {[{'type': r.record_type, 'title': r.title} for r in records]}"

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )

        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_test_recommendation(
                doctor=user, patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=prompt[:2000], output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )
        return result

    def _format_patient_context(self, patient) -> str:
        return (
            f"Name: {patient.name}\n"
            f"DOB: {patient.date_of_birth}\n"
            f"Gender: {patient.gender}\n"
            f"Branch: {patient.branch.name if patient.branch else 'N/A'}"
        )

    def _build_explanation_panel(self, response_text: str) -> dict:
        return {
            'reasoning': 'AI analyzed patient data including medical records, appointments, and uploaded documents.',
            'confidence': 'High - based on available structured data',
            'disclaimer': DISCLAIMER,
            'follow_up': 'Review the AI suggestion against the patient\'s full medical history before taking clinical action.',
        }


AgentRegistry.register('doctor', DoctorAgent)
