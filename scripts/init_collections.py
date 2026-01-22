"""
Initialize Qdrant collections for Healthcare Memory Assistant.

This script is IDEMPOTENT - safe to run multiple times.
It will only create collections/indexes if they don't exist.

Usage:
    python scripts/init_collections.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client.http import models

from app.db.qdrant_client import qdrant_manager
from app.db.collections import (
    COLLECTION_NAME,
    VECTOR_SIZE,
    DISTANCE_METRIC,
    IMAGE_COLLECTION_NAME,
    IMAGE_VECTOR_SIZE,
    get_payload_indexes,
    get_image_payload_indexes,
)


def init_collections() -> None:
    """Initialize both patient_memories and patient_images collections (idempotent)."""
    
    print("=" * 60)
    print("Healthcare Memory Assistant - Qdrant Initialization")
    print("=" * 60)
    
    # Check connection
    print("\n[1/5] Connecting to Qdrant...")
    try:
        health = qdrant_manager.client.get_collections()
        mode = "cloud" if hasattr(qdrant_manager, '_url') else "local"
        print(f"      ✓ Connected ({len(health.collections)} existing collections)")
    except Exception as e:
        print(f"      ✗ Connection failed: {e}")
        sys.exit(1)

    # Create text memories collection
    print(f"\n[2/5] Creating collection '{COLLECTION_NAME}'...")
    
    if qdrant_manager.collection_exists(COLLECTION_NAME):
        print(f"      ✓ Collection already exists (skipping)")
    else:
        qdrant_manager.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=DISTANCE_METRIC,
            ),
        )
        print(f"      ✓ Created collection")
        print(f"        - Vector size: {VECTOR_SIZE}")
        print(f"        - Distance: Cosine")

    # Create text payload indexes
    print(f"\n[3/5] Creating text memory payload indexes...")
    
    for index_def in get_payload_indexes():
        field_name = index_def["field_name"]
        try:
            qdrant_manager.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=index_def["schema"],
            )
            print(f"      ✓ Index: {field_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"      ✓ Index: {field_name} (exists)")
            else:
                print(f"      ⚠ Index: {field_name} - {e}")

    # Create image collection
    print(f"\n[4/5] Creating collection '{IMAGE_COLLECTION_NAME}'...")
    
    if qdrant_manager.collection_exists(IMAGE_COLLECTION_NAME):
        print(f"      ✓ Collection already exists (skipping)")
    else:
        qdrant_manager.client.create_collection(
            collection_name=IMAGE_COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=IMAGE_VECTOR_SIZE,
                distance=DISTANCE_METRIC,
            ),
        )
        print(f"      ✓ Created collection")
        print(f"        - Vector size: {IMAGE_VECTOR_SIZE} (CLIP ViT-B/32)")
        print(f"        - Distance: Cosine")

    # Create image payload indexes
    print(f"\n[5/5] Creating image payload indexes...")
    
    for index_def in get_image_payload_indexes():
        field_name = index_def["field_name"]
        try:
            qdrant_manager.client.create_payload_index(
                collection_name=IMAGE_COLLECTION_NAME,
                field_name=field_name,
                field_schema=index_def["schema"],
            )
            print(f"      ✓ Index: {field_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"      ✓ Index: {field_name} (exists)")
            else:
                print(f"      ⚠ Index: {field_name} - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Initialization complete!")
    print("=" * 60)
    
    print(f"\n📝 Collection: {COLLECTION_NAME}")
    print(f"   Vector size: {VECTOR_SIZE} (all-MiniLM-L6-v2)")
    print(f"   Modalities: text, document")
    
    print(f"\n🖼️  Collection: {IMAGE_COLLECTION_NAME}")
    print(f"   Vector size: {IMAGE_VECTOR_SIZE} (CLIP ViT-B/32)")
    print(f"   Modalities: image")
    
    print("\nPayload schema (both collections):")
    print("  - patient_id (keyword) [REQUIRED for isolation]")
    print("  - memory_type (keyword)")
    print("  - modality (keyword)")
    print("  - source (keyword)")
    print("  - created_at (datetime)")
    print("  - confidence (float)")
    print("  - metadata (json)")


if __name__ == "__main__":
    init_collections()

