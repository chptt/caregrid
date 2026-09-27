import logging

logger = logging.getLogger('ai')


class AILoggingMixin:
    """Mixin for AI-specific logging in views and services."""

    def log_request(self, agent_type: str, user: str, action: str, metadata: dict | None = None):
        logger.info("AI Request: agent=%s user=%s action=%s metadata=%s",
                     agent_type, user, action, metadata or {})

    def log_response(self, agent_type: str, user: str, tokens_used: int, success: bool):
        logger.info("AI Response: agent=%s user=%s tokens=%d success=%s",
                     agent_type, user, tokens_used, success)

    def log_error(self, agent_type: str, user: str, error: str):
        logger.error("AI Error: agent=%s user=%s error=%s", agent_type, user, error)
