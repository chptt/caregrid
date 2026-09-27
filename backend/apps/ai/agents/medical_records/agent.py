import logging
from typing import Any

from backend.apps.ai.agents.base.agent import BaseAgent
from backend.apps.ai.core.registry import AgentRegistry
from backend.apps.ai.providers.base import BaseLLMProvider
from backend.apps.ai.services.audit import AuditService

logger = logging.getLogger('ai')

DISCLAIMER = "AI Suggestion — Requires Doctor Verification"


class MedicalRecordsAgent(BaseAgent):
    agent_type = 'medical_records'
    description = 'Extract structured medical data from uploaded records'

    def __init__(self, llm_provider: BaseLLMProvider | None = None):
        super().__init__(llm_provider)

    def get_system_prompt(self, **kwargs) -> str:
        return self.prompt_manager.get('medical_records', 'system')

    def extract(self, document_text: str, filename: str = '',
                user=None, patient=None,
                conversation_id: str | None = None) -> dict[str, Any]:
        prompt = self.prompt_manager.get('medical_records', 'extract')
        prompt = prompt.replace('{document_text}', document_text[:15000])
        if filename:
            prompt = prompt.replace('{filename}', filename)

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )

        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_extraction(
                doctor=user,
                patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=document_text[:2000],
                output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )

        return result

    def summarize(self, document_text: str, filename: str = '',
                  user=None, patient=None,
                  conversation_id: str | None = None) -> dict[str, Any]:
        prompt = self.prompt_manager.get('medical_records', 'summarize')
        prompt = prompt.replace('{document_text}', document_text[:15000])
        if filename:
            prompt = prompt.replace('{filename}', filename)

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )

        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_summary(
                doctor=user,
                patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=document_text[:2000],
                output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )

        return result

    def analyze(self, document_text: str, filename: str = '',
                user=None, patient=None,
                conversation_id: str | None = None) -> dict[str, Any]:
        prompt = self.prompt_manager.get('medical_records', 'analyze')
        prompt = prompt.replace('{document_text}', document_text[:15000])
        if filename:
            prompt = prompt.replace('{filename}', filename)

        result = self.chat(
            user_message=prompt, user=user, patient=patient,
            conversation_id=conversation_id,
        )

        if 'error' not in result:
            agent_model = getattr(self.llm, 'model_name', 'unknown')
            AuditService.log_diagnosis_suggestion(
                doctor=user,
                patient=patient,
                conversation_id=result.get('conversation_id'),
                input_text=document_text[:2000],
                output_text=result.get('response', '')[:2000],
                ai_model=agent_model,
            )

        return result


AgentRegistry.register('medical_records', MedicalRecordsAgent)
