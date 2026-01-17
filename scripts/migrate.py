"""Migration utilities placeholder."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def migrate():
    """Run database migrations."""
    print("Migration utilities")
    print("-------------------")
    print("Currently, Qdrant doesn't require traditional migrations.")
    print("Use init_collections.py to set up the schema.")
    print("\nAvailable operations:")
    print("  - python scripts/init_collections.py  # Initialize collections")
    print("  - python scripts/seed_data.py         # Seed sample data")


if __name__ == "__main__":
    asyncio.run(migrate())
