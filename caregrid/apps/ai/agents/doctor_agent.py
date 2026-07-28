import logging
from .base import BaseAgent
from caregrid.apps.ai.rag.retriever import Retriever
from core.models import Patient, Appointment, Doctor

logger = logging.getLogger('ai')


class DoctorAssistant(BaseAgent):
    """AI assistant for doctors - provides clinical decision support."""

    agent_type = 'doctor'
    description = 'Clinical decision support, patient history summaries, and visit documentation'

    def __init__(self):
        super().__init__()
        self.retriever = Retriever()

    def get_system_prompt(self, **kwargs) -> str:
        base = self.prompt_manager.get_prompt('doctor', 'system')

        patient_ctx = kwargs.get('patient_context')
        if patient_ctx:
            patient_info = self._build_patient_context(patient_ctx)
            base += f"\n\nCurrent Patient Context:\n{patient_info}"

        rag_context = kwargs.get('rag_context', '')
        if rag_context:
            base += f"\n\nRelevant Clinical References:\n{rag_context}"

        return base

    def summarize_patient_history(self, patient_id: int, user=None) -> dict:
        """Generate a summary of patient history."""
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        appointments = Appointment.objects.filter(patient=patient).order_by('-date')[:10]
        appointment_data = []
        for apt in appointments:
            appointment_data.append({
                'doctor': apt.doctor.name,
                'specialization': apt.doctor.specialization,
                'date': str(apt.date),
                'time': str(apt.time),
            })

        prompt = self.prompt_manager.get_prompt('doctor', 'summarize_history')
        prompt += f"\n\nPatient: {patient.name}, DOB: {patient.date_of_birth}, Gender: {patient.gender}"
        prompt += f"\nRecent Appointments: {appointment_data}"

        messages = [
            {'role': 'system', 'content': self.get_system_prompt()},
            {'role': 'user', 'content': prompt},
        ]

        try:
            summary = self.llm.generate(messages)
            return {
                'patient_id': patient_id,
                'patient_name': patient.name,
                'summary': summary,
                'appointments_analyzed': len(appointment_data),
            }
        except Exception as e:
            logger.error("Failed to summarize patient history: %s", e)
            return {'error': str(e)}

    def generate_visit_summary(self, patient_id: int, visit_notes: str,
                               doctor_notes: str = '', user=None) -> dict:
        """Generate a structured visit summary."""
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return {'error': 'Patient not found'}

        prompt = self.prompt_manager.get_prompt('doctor', 'visit_summary')
        prompt += f"\n\nPatient: {patient.name}"
        prompt += f"\nVisit Notes: {visit_notes}"
        if doctor_notes:
            prompt += f"\nDoctor's Notes: {doctor_notes}"

        messages = [
            {'role': 'system', 'content': self.get_system_prompt()},
            {'role': 'user', 'content': prompt},
        ]

        try:
            summary = self.llm.generate(messages)
            return {
                'patient_id': patient_id,
                'visit_summary': summary,
                'status': 'generated',
                'note': 'This summary requires doctor approval before being saved.',
            }
        except Exception as e:
            logger.error("Failed to generate visit summary: %s", e)
            return {'error': str(e)}

    def _build_patient_context(self, patient) -> str:
        if isinstance(patient, int):
            try:
                patient = Patient.objects.get(id=patient)
            except Patient.DoesNotExist:
                return "Patient information unavailable"
        return (
            f"Name: {patient.name}\n"
            f"DOB: {patient.date_of_birth}\n"
            f"Gender: {patient.gender}\n"
            f"Branch: {patient.branch.name if patient.branch else 'N/A'}"
        )
