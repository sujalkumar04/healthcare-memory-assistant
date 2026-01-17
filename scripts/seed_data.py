"""Seed test data for development."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.qdrant_client import qdrant_manager
from app.memory import memory_manager
from app.schemas import MemoryCreate, MemorySource, MemoryType


SAMPLE_MEMORIES = [
    {
        "patient_id": "patient_001",
        "content": "Patient reported experiencing anxiety and difficulty sleeping for the past two weeks.",
        "memory_type": MemoryType.MENTAL_HEALTH,
        "source": MemorySource.SESSION,
    },
    {
        "patient_id": "patient_001",
        "content": "Prescribed Sertraline 50mg daily for anxiety management.",
        "memory_type": MemoryType.MEDICATION,
        "source": MemorySource.NOTE,
    },
    {
        "patient_id": "patient_001",
        "content": "Blood pressure reading: 120/80 mmHg. Heart rate: 72 bpm.",
        "memory_type": MemoryType.CLINICAL,
        "source": MemorySource.SESSION,
    },
    {
        "patient_id": "patient_001",
        "content": "Patient mentioned starting a new exercise routine, walking 30 minutes daily.",
        "memory_type": MemoryType.LIFESTYLE,
        "source": MemorySource.CONVERSATION,
    },
    {
        "patient_id": "patient_002",
        "content": "Follow-up appointment for diabetes management. HbA1c level at 6.8%.",
        "memory_type": MemoryType.CLINICAL,
        "source": MemorySource.SESSION,
    },
    {
        "patient_id": "patient_002",
        "content": "Patient reports improved mood after starting regular meditation practice.",
        "memory_type": MemoryType.MENTAL_HEALTH,
        "source": MemorySource.SESSION,
    },
]


async def seed_data():
    """Seed the database with sample data."""
    print("Connecting to Qdrant...")
    await qdrant_manager.connect()

    print("Seeding sample memories...")
    for memory_data in SAMPLE_MEMORIES:
        memory = MemoryCreate(**memory_data)
        result = await memory_manager.store_memory(memory)
        print(f"  Created memory {result.id} for {memory.patient_id}")

    print(f"\nSeeded {len(SAMPLE_MEMORIES)} memories successfully!")

    await qdrant_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_data())
