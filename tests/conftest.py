"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_memory():
    """Sample memory data for testing."""
    return {
        "patient_id": "test_patient_001",
        "content": "Test memory content for unit testing.",
        "memory_type": "clinical",
        "source": "session",
        "metadata": {"test": True},
    }


@pytest.fixture
def sample_search():
    """Sample search request for testing."""
    return {
        "patient_id": "test_patient_001",
        "query": "test query",
        "limit": 10,
        "min_score": 0.5,
    }
