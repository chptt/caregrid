import logging
from .base import BaseAgent

logger = logging.getLogger('ai')


class PatientAssistant(BaseAgent):
    """AI assistant for patients - provides health information in simple language."""

    agent_type = 'patient'
    description = 'Patient-facing health information and guidance in simple, non-medical language'

    def get_system_prompt(self, **kwargs) -> str:
        return self.prompt_manager.get_prompt('patient', 'system')

    def explain_diagnosis(self, diagnosis_text: str, conversation_id=None,
                          user=None) -> dict:
        """Explain a diagnosis in patient-friendly language."""
        prompt = self.prompt_manager.get_prompt('patient', 'explain_diagnosis')
        prompt += f"\n\nDiagnosis to explain:\n{diagnosis_text}"

        return self.chat(
            user_message=prompt,
            conversation_id=conversation_id,
            user=user,
        )

    def medication_info(self, medication_name: str, dosage: str = '',
                        conversation_id=None, user=None) -> dict:
        """Provide patient-friendly medication information."""
        prompt = self.prompt_manager.get_prompt('patient', 'medication_info')
        prompt += f"\n\nMedication: {medication_name}"
        if dosage:
            prompt += f"\nDosage: {dosage}"

        return self.chat(
            user_message=prompt,
            conversation_id=conversation_id,
            user=user,
        )

    def general_health_query(self, question: str, conversation_id=None,
                             user=None) -> dict:
        """Answer a general health question in simple language."""
        prompt = self.prompt_manager.get_prompt('patient', 'general_health')
        prompt += f"\n\nPatient's question: {question}"

        return self.chat(
            user_message=prompt,
            conversation_id=conversation_id,
            user=user,
        )
