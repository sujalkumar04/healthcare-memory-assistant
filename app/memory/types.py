"""Memory type definitions."""

from enum import Enum


class MemoryCategory(str, Enum):
    """Categories for healthcare memories."""

    CLINICAL = "clinical"
    MENTAL_HEALTH = "mental_health"
    MEDICATION = "medication"
    LIFESTYLE = "lifestyle"
    SYMPTOM = "symptom"
    APPOINTMENT = "appointment"
    GENERAL = "general"


class MemoryPriority(str, Enum):
    """Priority levels for memories."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Memory type configurations
MEMORY_TYPE_CONFIG = {
    MemoryCategory.CLINICAL: {
        "retention_days": 3650,  # 10 years
        "priority_boost": 1.2,
    },
    MemoryCategory.MENTAL_HEALTH: {
        "retention_days": 1825,  # 5 years
        "priority_boost": 1.1,
    },
    MemoryCategory.MEDICATION: {
        "retention_days": 3650,
        "priority_boost": 1.15,
    },
    MemoryCategory.SYMPTOM: {
        "retention_days": 365,
        "priority_boost": 1.0,
    },
    MemoryCategory.APPOINTMENT: {
        "retention_days": 365,
        "priority_boost": 0.9,
    },
    MemoryCategory.GENERAL: {
        "retention_days": 180,
        "priority_boost": 0.8,
    },
}
