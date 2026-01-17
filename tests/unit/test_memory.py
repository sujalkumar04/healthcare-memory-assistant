"""Unit tests for memory module."""

import pytest
from app.schemas import MemoryCreate, MemoryType, MemorySource


class TestMemoryCreate:
    """Tests for MemoryCreate schema."""

    def test_valid_memory_create(self):
        """Test creating a valid memory."""
        memory = MemoryCreate(
            patient_id="patient_001",
            content="Test content",
            memory_type=MemoryType.CLINICAL,
            source=MemorySource.SESSION,
        )
        assert memory.patient_id == "patient_001"
        assert memory.content == "Test content"
        assert memory.memory_type == MemoryType.CLINICAL

    def test_memory_create_defaults(self):
        """Test memory create with defaults."""
        memory = MemoryCreate(
            patient_id="patient_001",
            content="Test content",
        )
        assert memory.memory_type == MemoryType.GENERAL
        assert memory.source == MemorySource.CONVERSATION
        assert memory.metadata == {}

    def test_memory_create_empty_content_fails(self):
        """Test that empty content fails validation."""
        with pytest.raises(ValueError):
            MemoryCreate(
                patient_id="patient_001",
                content="",
            )
