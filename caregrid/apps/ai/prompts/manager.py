import os
import logging
from pathlib import Path

logger = logging.getLogger('ai')


class PromptManager:
    """Manages prompt templates from external files."""

    def __init__(self):
        self.template_dir = Path(__file__).resolve().parent / 'templates'
        self._cache = {}

    def get_prompt(self, agent_type: str, template_name: str, **kwargs) -> str:
        """Load and return a prompt template with variable substitution."""
        cache_key = f"{agent_type}:{template_name}"

        if cache_key not in self._cache:
            template_path = self.template_dir / agent_type / f'{template_name}.txt'
            if not template_path.exists():
                logger.error("Prompt template not found: %s", template_path)
                return f"[Missing template: {agent_type}/{template_name}]"

            with open(template_path, 'r', encoding='utf-8') as f:
                self._cache[cache_key] = f.read()

        prompt = self._cache[cache_key]

        if kwargs:
            for key, value in kwargs.items():
                prompt = prompt.replace(f'{{{key}}}', str(value))

        return prompt

    def reload_templates(self):
        """Clear template cache and reload on next access."""
        self._cache.clear()

    def list_templates(self) -> dict:
        """List all available templates by agent type."""
        templates = {}
        if not self.template_dir.exists():
            return templates

        for agent_dir in self.template_dir.iterdir():
            if agent_dir.is_dir():
                agent_templates = [
                    f.stem for f in agent_dir.glob('*.txt')
                ]
                templates[agent_dir.name] = agent_templates

        return templates
