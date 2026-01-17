"""API Request/Response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# MEMORY INGESTION
# =============================================================================

class PatientProfile(BaseModel):
    """Synthetic patient profile."""
    full_name: str | None = None
    sex: str | None = None
    age_range: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    department: str | None = None
    first_visit: str | None = None


class VisitMetadata(BaseModel):
    """Visit-specific context."""
    visit_type: str | None = None
    visit_date: str | None = None
    clinician_role: str | None = None


class MemoryIngestRequest(BaseModel):
    """Request for ingesting a new memory."""
    patient_id: str = Field(..., min_length=1, description="Patient identifier")
    raw_text: str = Field(..., min_length=1, description="Memory content to ingest")
    memory_type: str = Field(
        default="note",
        description="Memory type: clinical | mental_health | medication | note | attachment"
    )
    source: str = Field(
        default="session",
        description="Memory source: session | doctor | import"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")
    profile: PatientProfile | None = Field(default=None, description="Patient demographics")
    visit: VisitMetadata | None = Field(default=None, description="Visit context")


class MemoryIngestResponse(BaseModel):
    """Response from memory ingestion."""
    action: str = Field(..., description="Action taken: created | reinforced")
    point_ids: list[str] = Field(..., description="Created/reinforced memory IDs")
    chunks_stored: int = Field(..., description="Number of chunks stored")
    patient_id: str


# =============================================================================
# SEARCH / RETRIEVAL
# =============================================================================

class SearchRequest(BaseModel):
    """Request for semantic search."""
    patient_id: str = Field(..., min_length=1, description="Patient identifier")
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    memory_types: list[str] | None = Field(default=None, description="Filter by types")


class EvidenceItem(BaseModel):
    """Single evidence item in search results."""
    content: str
    semantic_score: float
    confidence: float
    combined_score: float
    source: str
    memory_type: str
    created_at: str
    point_id: str
    parent_id: str | None = None
    chunk_index: int | None = None


class SearchResponse(BaseModel):
    """Response from search."""
    query: str
    patient_id: str
    total_found: int
    evidence: list[EvidenceItem]


# =============================================================================
# GROUNDED ANSWER
# =============================================================================

class ContextSearchRequest(BaseModel):
    """Request for search with LLM-generated answer."""
    patient_id: str = Field(..., min_length=1, description="Patient identifier")
    query: str = Field(..., min_length=1, description="Question to answer")
    mode: str = Field(
        default="general",
        description="Reasoning mode: general | mental_health"
    )


class ContextSearchResponse(BaseModel):
    """Response with grounded answer."""
    answer_text: str
    has_context: bool
    evidence_count: int
    sources_used: list[str]
    disclaimer: str
    query: str
    patient_id: str


# =============================================================================
# PATIENT SUMMARY
# =============================================================================

class PatientSummaryResponse(BaseModel):
    """Response for patient summary."""
    patient_id: str
    summary: str
    memory_count: int
    has_context: bool
    disclaimer: str


# =============================================================================
# HEALTH CHECK
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    qdrant: str
    version: str = "0.1.0"


class SuggestionResponse(BaseModel):
    """Response for smart suggestions."""
    patient_id: str
    suggestions: list[str]
    based_on_count: int
