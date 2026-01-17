"""Utility helpers."""

from datetime import datetime
from typing import Any
from uuid import UUID


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format."""
    return dt.isoformat()


def serialize_uuid(uuid: UUID) -> str:
    """Serialize UUID to string."""
    return str(uuid)


def clean_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from a dictionary."""
    return {k: v for k, v in d.items() if v is not None}


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
