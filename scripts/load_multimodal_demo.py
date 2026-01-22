"""
Multimodal Demo Data Loader

Loads sample text, document, and image data for demonstration.
Creates a complete multimodal patient record for testing retrieval.

Usage:
    python scripts/load_multimodal_demo.py
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# DEMO DATA
# =============================================================================

DEMO_PATIENT_ID = "demo_multimodal_001"

# Sample TEXT memories (existing text modality)
TEXT_MEMORIES = [
    {
        "content": "Patient presents with persistent cough for 2 weeks. No fever. Reports mild fatigue. Non-smoker. Vitals normal.",
        "memory_type": "clinical",
        "source": "session",
    },
    {
        "content": "Prescribed amoxicillin 500mg TID for 7 days for suspected upper respiratory infection. Follow-up in 1 week.",
        "memory_type": "medication",
        "source": "doctor",
    },
    {
        "content": "Patient reports improved mood after starting regular exercise routine. Sleep quality better. Stress levels manageable.",
        "memory_type": "mental_health",
        "source": "session",
    },
]

# Sample DOCUMENT content (simulating PDF extraction)
DOCUMENT_CONTENT = """
LABORATORY REPORT - COMPLETE BLOOD COUNT

Patient ID: demo_multimodal_001
Date: 2026-01-15

TEST RESULTS:
- White Blood Cells (WBC): 7.2 x10^9/L (Normal: 4.5-11.0)
- Red Blood Cells (RBC): 4.8 x10^12/L (Normal: 4.5-5.5)
- Hemoglobin: 14.2 g/dL (Normal: 13.5-17.5)
- Hematocrit: 42% (Normal: 38-50%)
- Platelets: 245 x10^9/L (Normal: 150-400)

INTERPRETATION:
All values within normal limits. No signs of infection or anemia.

Signed: Dr. Sarah Johnson, MD
Lab ID: LAB-2026-0115-001
"""

# Sample IMAGE metadata (simulating uploaded image)
IMAGE_METADATA = {
    "description": "Chest X-ray anterior-posterior view, taken 2026-01-10",
    "memory_type": "clinical",
    "original_filename": "chest_xray_2026_01_10.jpg",
    "width": 1024,
    "height": 768,
    "format": "JPEG",
}


# =============================================================================
# LOADING FUNCTIONS
# =============================================================================

async def load_text_memories():
    """Load sample text memories."""
    from app.memory.manager import memory_manager
    
    print("\n📝 Loading TEXT memories...")
    
    for i, mem in enumerate(TEXT_MEMORIES, 1):
        result = await memory_manager.ingest_memory(
            patient_id=DEMO_PATIENT_ID,
            raw_text=mem["content"],
            memory_type=mem["memory_type"],
            source=mem["source"],
            modality="text",
            check_reinforcement=False,
        )
        print(f"   [{i}] {mem['memory_type']}: {result['action']} ({len(result['point_ids'])} chunks)")
    
    print(f"   ✓ Loaded {len(TEXT_MEMORIES)} text memories")


async def load_document_memory():
    """Load sample document (simulated PDF content)."""
    from app.memory.manager import memory_manager
    
    print("\n📄 Loading DOCUMENT memory...")
    
    result = await memory_manager.ingest_memory(
        patient_id=DEMO_PATIENT_ID,
        raw_text=DOCUMENT_CONTENT,
        memory_type="clinical",
        source="pdf",
        modality="document",
        metadata={
            "original_filename": "lab_report_2026_01_15.pdf",
            "page_count": 1,
            "extraction_method": "simulated",
        },
        check_reinforcement=False,
    )
    print(f"   ✓ Loaded lab report: {result['action']} ({len(result['point_ids'])} chunks)")


async def load_image_memory():
    """Load sample image metadata (simulated CLIP embedding)."""
    from app.db.image_operations import image_ops
    import random
    
    print("\n🖼️  Loading IMAGE memory...")
    
    # Generate simulated 512-dim CLIP embedding
    # In production, this would come from the actual CLIP model
    simulated_embedding = [random.uniform(-0.1, 0.1) for _ in range(512)]
    
    point_id = await image_ops.upsert_image(
        vector=simulated_embedding,
        patient_id=DEMO_PATIENT_ID,
        description=IMAGE_METADATA["description"],
        memory_type=IMAGE_METADATA["memory_type"],
        source="upload",
        confidence=1.0,
        metadata={
            "original_filename": IMAGE_METADATA["original_filename"],
            "width": IMAGE_METADATA["width"],
            "height": IMAGE_METADATA["height"],
            "format": IMAGE_METADATA["format"],
            "file_size_bytes": 256000,
            "embedding_model": "simulated",
            "is_active": True,
        },
    )
    print(f"   ✓ Loaded chest X-ray: {point_id}")


async def main():
    """Load all multimodal demo data."""
    print("=" * 60)
    print("MULTIMODAL DEMO DATA LOADER")
    print("=" * 60)
    print(f"\nPatient ID: {DEMO_PATIENT_ID}")
    
    await load_text_memories()
    await load_document_memory()
    await load_image_memory()
    
    print("\n" + "=" * 60)
    print("DEMO DATA LOADED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nModalities loaded:")
    print(f"  • TEXT: {len(TEXT_MEMORIES)} memories")
    print(f"  • DOCUMENT: 1 lab report (PDF)")
    print(f"  • IMAGE: 1 chest X-ray")
    print(f"\nPatient ID for queries: {DEMO_PATIENT_ID}")


if __name__ == "__main__":
    asyncio.run(main())
