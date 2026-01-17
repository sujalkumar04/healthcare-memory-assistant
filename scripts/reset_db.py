"""
Reset Qdrant collection (DELETE ALL DATA) and re-initialize.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.qdrant_client import qdrant_manager
from app.db.collections import COLLECTION_NAME
from scripts.init_collections import init_collections

def reset_db():
    print("=" * 60)
    print("⚠️  DANGER ZONE: DELETING ALL PATIENT DATA")
    print("=" * 60)
    
    # confirmation = input(f"Are you sure you want to delete collection '{COLLECTION_NAME}'? (y/n): ")
    # if confirmation.lower() != 'y':
    #     print("Aborted.")
    #     return

    print(f"\n[1/2] Deleting collection '{COLLECTION_NAME}'...")
    try:
        qdrant_manager.client.delete_collection(COLLECTION_NAME)
        print("      ✓ Collection deleted")
    except Exception as e:
        print(f"      ⚠  Failed to delete (might not exist): {e}")

    print("\n[2/2] Re-initializing...")
    init_collections()

if __name__ == "__main__":
    reset_db()
