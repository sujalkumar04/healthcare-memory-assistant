"""Pydantic schemas for search operations."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.memory import MemoryResponse, MemoryType, Modality


class SearchRequest(BaseModel):
    """Schema for semantic search request."""

    patient_id: str = Field(..., description="Patient ID to search within")
    query: str = Field(..., min_length=1, description="Search query text")
    memory_types: list[MemoryType] | None = Field(
        default=None, description="Filter by memory types"
    )
    modalities: list[Modality] | None = Field(
        default=None, description="Filter by modalities (text, document, image)"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max results to return")
    min_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    date_from: datetime | None = Field(default=None, description="Filter memories from this date")
    date_to: datetime | None = Field(default=None, description="Filter memories to this date")


class SearchResponse(BaseModel):
    """Schema for search response."""

    results: list[MemoryResponse]
    query: str
    patient_id: str
    total_found: int


class SearchWithContextRequest(BaseModel):
    """Schema for search with LLM context generation."""

    patient_id: str = Field(..., description="Patient ID to search within")
    query: str = Field(..., min_length=1, description="Search query text")
    include_summary: bool = Field(default=True, description="Include LLM-generated summary")
    limit: int = Field(default=10, ge=1, le=100, description="Max results to return")


class SearchWithContextResponse(BaseModel):
    """Schema for search with context response."""

    results: list[MemoryResponse]
    summary: str | None = None
    query: str
    patient_id: str
