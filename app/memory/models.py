"""Memory data models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.memory.types import MemoryCategory


class Memory(BaseModel):
    """Internal memory representation."""

    id: UUID
    patient_id: str
    content: str
    category: MemoryCategory
    source: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None
    score: float | None = None


class PatientContext(BaseModel):
    """Context for a patient session."""

    patient_id: str
    session_id: str | None = None
    recent_memories: list[Memory] = Field(default_factory=list)
    active_topics: list[str] = Field(default_factory=list)
    last_interaction: datetime | None = None
