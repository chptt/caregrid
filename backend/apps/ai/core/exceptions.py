class AIError(Exception):
    """Base exception for AI module."""


class ProviderError(AIError):
    """Raised when LLM provider fails."""


class DocumentProcessingError(AIError):
    """Raised when document processing fails."""


class EmbeddingError(AIError):
    """Raised when embedding generation fails."""


class AgentError(AIError):
    """Raised when agent encounters an error."""
