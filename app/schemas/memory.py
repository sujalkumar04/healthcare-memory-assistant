"""Pydantic schemas for memory operations."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of healthcare memories."""

    CLINICAL = "clinical"
    MENTAL_HEALTH = "mental_health"
    MEDICATION = "medication"
    LIFESTYLE = "lifestyle"
    SYMPTOM = "symptom"
    APPOINTMENT = "appointment"
    GENERAL = "general"


class MemorySource(str, Enum):
    """Source of the memory."""

    SESSION = "session"
    NOTE = "note"
    IMPORT = "import"
    CONVERSATION = "conversation"


class MemoryCreate(BaseModel):
    """Schema for creating a new memory."""

    patient_id: str = Field(..., description="Unique patient identifier")
    content: str = Field(..., min_length=1, description="Memory content text")
    memory_type: MemoryType = Field(default=MemoryType.GENERAL, description="Type of memory")
    source: MemorySource = Field(default=MemorySource.CONVERSATION, description="Memory source")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MemoryResponse(BaseModel):
    """Schema for memory response."""

    id: UUID
    patient_id: str
    content: str
    memory_type: MemoryType
    source: MemorySource
    created_at: datetime
    metadata: dict[str, Any]
    score: float | None = None  # Relevance score for search results


class MemoryList(BaseModel):
    """Schema for list of memories."""

    memories: list[MemoryResponse]
    total: int
    patient_id: str
