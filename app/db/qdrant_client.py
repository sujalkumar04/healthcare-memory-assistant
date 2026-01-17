"""Qdrant client abstraction with cloud and Docker compatibility."""

import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.core.exceptions import QdrantConnectionError


class QdrantManager:
    """
    Manages Qdrant client connection.
    
    Cloud-ready: Works with both local Docker and Qdrant Cloud.
    - Local: Uses host + port
    - Cloud: Uses url + api_key
    """

    def __init__(self):
        self._client: QdrantClient | None = None

    @property
    def client(self) -> QdrantClient:
        """Get the Qdrant client (lazy initialization)."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> QdrantClient:
        """
        Create Qdrant client based on environment.
        
        Priority:
        1. QDRANT_URL (for Qdrant Cloud)
        2. QDRANT_HOST + QDRANT_PORT (for Docker/local)
        3. In-memory mode (for development without Docker)
        """
        qdrant_url = settings.QDRANT_URL  # Read from settings (loaded from .env)
        api_key = settings.QDRANT_API_KEY
        use_memory = os.getenv("QDRANT_MEMORY", "false").lower() == "true"

        try:
            if use_memory:
                # In-memory mode for development/testing
                return QdrantClient(":memory:")
            elif qdrant_url:
                # Qdrant Cloud mode
                print(f"🌐 Connecting to Qdrant Cloud: {qdrant_url[:50]}...")
                return QdrantClient(
                    url=qdrant_url,
                    api_key=api_key,
                    timeout=30,
                )
            else:
                # Local Docker mode - try to connect, fallback to memory
                try:
                    client = QdrantClient(
                        host=settings.QDRANT_HOST,
                        port=settings.QDRANT_PORT,
                        api_key=api_key if api_key else None,
                        timeout=5,
                    )
                    # Test connection
                    client.get_collections()
                    return client
                except Exception:
                    # Fallback to in-memory if Docker not available
                    print("⚠️  Qdrant not reachable, using in-memory mode")
                    return QdrantClient(":memory:")
        except Exception as e:
            raise QdrantConnectionError(f"Failed to create Qdrant client: {e}")

    async def connect(self) -> None:
        """Initialize and verify connection."""
        try:
            # Force client creation and verify
            _ = self.client.get_collections()
        except Exception as e:
            raise QdrantConnectionError(f"Failed to connect to Qdrant: {e}")

    async def disconnect(self) -> None:
        """Close the Qdrant connection."""
        if self._client:
            self._client.close()
            self._client = None

    async def health_check(self) -> dict[str, Any]:
        """Check Qdrant health status."""
        try:
            collections = self.client.get_collections()
            return {
                "status": "healthy",
                "collections_count": len(collections.collections),
                "mode": "cloud" if os.getenv("QDRANT_URL") else "local",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == name for c in collections)
        except Exception:
            return False


# Singleton instance
qdrant_manager = QdrantManager()
