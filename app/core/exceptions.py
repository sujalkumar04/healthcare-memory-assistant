"""Custom exception classes."""

from typing import Any


class HealthcareMemoryException(Exception):
    """Base exception for Healthcare Memory Assistant."""

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class PatientNotFoundError(HealthcareMemoryException):
    """Raised when a patient is not found."""

    pass


class MemoryNotFoundError(HealthcareMemoryException):
    """Raised when a memory is not found."""

    pass


class EmbeddingError(HealthcareMemoryException):
    """Raised when embedding generation fails."""

    pass


class QdrantConnectionError(HealthcareMemoryException):
    """Raised when Qdrant connection fails."""

    pass


class LLMError(HealthcareMemoryException):
    """Raised when LLM operations fail."""

    pass


class AuthenticationError(HealthcareMemoryException):
    """Raised when authentication fails."""

    pass


class RateLimitError(HealthcareMemoryException):
    """Raised when rate limit is exceeded."""

    pass
