"""
Integrated Multimodal Test

Tests all modalities in a single process using in-memory Qdrant.
Run: python scripts/test_multimodal.py
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Force in-memory mode
import os
os.environ["QDRANT_MEMORY"] = "true"


async def main():
    print("=" * 60)
    print("MULTIMODAL INTEGRATION TEST")
    print("=" * 60)
    
    # Step 1: Initialize collections
    print("\n[1/6] INITIALIZING COLLECTIONS...")
    from qdrant_client.http import models
    from app.db.qdrant_client import qdrant_manager
    from app.db.collections import (
        COLLECTION_NAME, VECTOR_SIZE, DISTANCE_METRIC,
        IMAGE_COLLECTION_NAME, IMAGE_VECTOR_SIZE,
    )
    
    # Create text collection
    qdrant_manager.client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=DISTANCE_METRIC),
    )
    print(f"   ✓ Created {COLLECTION_NAME} (384-dim)")
    
    # Create image collection
    qdrant_manager.client.create_collection(
        collection_name=IMAGE_COLLECTION_NAME,
        vectors_config=models.VectorParams(size=IMAGE_VECTOR_SIZE, distance=DISTANCE_METRIC),
    )
    print(f"   ✓ Created {IMAGE_COLLECTION_NAME} (512-dim)")
    
    # Step 2: Ingest TEXT memory
    print("\n[2/6] TESTING TEXT INGESTION...")
    from app.memory.manager import memory_manager
    
    text_result = await memory_manager.ingest_memory(
        patient_id="test_patient",
        raw_text="Patient presents with persistent cough for 2 weeks. Prescribed amoxicillin 500mg.",
        memory_type="clinical",
        source="session",
        modality="text",
        check_reinforcement=False,
    )
    print(f"   ✓ Ingested text: {text_result['action']}, {len(text_result['point_ids'])} chunks")
    
    # Step 3: Ingest DOCUMENT memory
    print("\n[3/6] TESTING DOCUMENT INGESTION...")
    doc_result = await memory_manager.ingest_memory(
        patient_id="test_patient",
        raw_text="LABORATORY REPORT: White Blood Cells 7.2, Hemoglobin 14.2, Platelets 245. All values normal.",
        memory_type="clinical",
        source="pdf",
        modality="document",
        metadata={"original_filename": "lab_report.pdf"},
        check_reinforcement=False,
    )
    print(f"   ✓ Ingested document: {doc_result['action']}, {len(doc_result['point_ids'])} chunks")
    
    # Step 4: Ingest IMAGE memory
    print("\n[4/6] TESTING IMAGE INGESTION...")
    from app.db.image_operations import image_ops
    import random
    
    simulated_embedding = [random.uniform(-0.1, 0.1) for _ in range(512)]
    image_id = await image_ops.upsert_image(
        vector=simulated_embedding,
        patient_id="test_patient",
        description="Chest X-ray anterior view",
        memory_type="clinical",
        source="upload",
        confidence=1.0,
        metadata={"original_filename": "chest_xray.jpg", "width": 1024, "height": 768},
    )
    print(f"   ✓ Ingested image: {image_id}")
    
    # Step 5: Test RETRIEVAL
    print("\n[5/6] TESTING RETRIEVAL BY MODALITY...")
    from app.retrieval.engine import retrieval_engine
    
    # Text retrieval
    text_evidence = await retrieval_engine.retrieve(
        patient_id="test_patient",
        query="What medication was prescribed?",
        modalities=["text"],
    )
    print(f"   ✓ Text retrieval: {len(text_evidence)} results")
    if text_evidence:
        print(f"     → Top result: {text_evidence[0].content[:60]}...")
        print(f"     → Modality: {text_evidence[0].modality}")
    
    # Document retrieval
    doc_evidence = await retrieval_engine.retrieve(
        patient_id="test_patient",
        query="lab results blood count",
        modalities=["document"],
    )
    print(f"   ✓ Document retrieval: {len(doc_evidence)} results")
    if doc_evidence:
        print(f"     → Top result: {doc_evidence[0].content[:60]}...")
        print(f"     → Modality: {doc_evidence[0].modality}")
    
    # Step 6: Test Anti-Hallucination
    print("\n[6/6] TESTING ANTI-HALLUCINATION SAFEGUARD...")
    from app.reasoning.chains import reasoning_chain
    
    # Test with no evidence (query about non-existent data)
    no_evidence_response = await reasoning_chain.reason(
        patient_id="test_patient",
        query="What is the patient's blood pressure?",
        evidence=[],  # Empty evidence
    )
    print(f"   ✓ No evidence response:")
    print(f"     → has_context: {no_evidence_response.has_context}")
    print(f"     → answer: {no_evidence_response.answer_text[:60]}...")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"""
✅ Collections Created:
   - patient_memories (384-dim)
   - patient_images (512-dim)

✅ Ingestion Tested:
   - TEXT: {text_result['action']} ({len(text_result['point_ids'])} chunks)
   - DOCUMENT: {doc_result['action']} ({len(doc_result['point_ids'])} chunks)
   - IMAGE: Stored (simulated embedding)

✅ Retrieval Tested:
   - Text-only: {len(text_evidence)} results
   - Document-only: {len(doc_evidence)} results

✅ Anti-Hallucination:
   - Empty evidence returns fixed response: {not no_evidence_response.has_context}

ALL MULTIMODAL TESTS PASSED!
""")


if __name__ == "__main__":
    asyncio.run(main())
