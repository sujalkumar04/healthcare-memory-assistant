"""API v1 endpoints module."""

from app.api.v1.endpoints import health, memory, patient, search

__all__ = ["health", "memory", "patient", "search"]
