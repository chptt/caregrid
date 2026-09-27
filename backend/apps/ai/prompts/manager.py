import os
import logging
from pathlib import Path

logger = logging.getLogger('ai')


class PromptManager:
    def __init__(self):
        self._template_dir = Path(__file__).resolve().parent / 'templates'
        self._cache: dict[str, str] = {}

    def get(self, agent_type: str, template_name: str, **kwargs) -> str:
        cache_key = f"{agent_type}:{template_name}"
        if cache_key not in self._cache:
            template_path = self._template_dir / agent_type / f'{template_name}.txt'
            if not template_path.exists():
                logger.error("Prompt template missing: %s", template_path)
                return f"[Template not found: {agent_type}/{template_name}]"
            with open(template_path, 'r', encoding='utf-8') as f:
                self._cache[cache_key] = f.read()

        prompt = self._cache[cache_key]
        if kwargs:
            for key, value in kwargs.items():
                prompt = prompt.replace(f'{{{key}}}', str(value))
        return prompt

    def reload(self):
        self._cache.clear()
