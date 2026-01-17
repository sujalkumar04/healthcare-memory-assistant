"""Pydantic schemas for patient operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    """Schema for creating a new patient."""

    patient_id: str = Field(..., description="Unique patient identifier")
    name: str = Field(..., min_length=1, description="Patient name")
    metadata: dict = Field(default_factory=dict, description="Additional patient metadata")


class PatientResponse(BaseModel):
    """Schema for patient response."""

    patient_id: str
    name: str
    created_at: datetime
    memory_count: int = 0
    metadata: dict


class PatientList(BaseModel):
    """Schema for list of patients."""

    patients: list[PatientResponse]
    total: int
