"""Query filter builders for Qdrant."""

from datetime import datetime

from qdrant_client.http import models


def build_patient_filter(patient_id: str) -> models.FieldCondition:
    """Build a filter for patient ID."""
    return models.FieldCondition(
        key="patient_id",
        match=models.MatchValue(value=patient_id),
    )


def build_memory_type_filter(memory_types: list[str]) -> models.FieldCondition:
    """Build a filter for memory types."""
    return models.FieldCondition(
        key="memory_type",
        match=models.MatchAny(any=memory_types),
    )


def build_date_range_filter(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[models.FieldCondition]:
    """Build date range filters."""
    filters = []

    if date_from:
        filters.append(
            models.FieldCondition(
                key="created_at",
                range=models.Range(gte=date_from.isoformat()),
            )
        )

    if date_to:
        filters.append(
            models.FieldCondition(
                key="created_at",
                range=models.Range(lte=date_to.isoformat()),
            )
        )

    return filters


def combine_filters(conditions: list[models.FieldCondition]) -> models.Filter:
    """Combine multiple filter conditions with AND logic."""
    return models.Filter(must=conditions)
