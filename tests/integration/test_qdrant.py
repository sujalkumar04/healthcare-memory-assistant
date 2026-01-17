"""Integration tests for Qdrant operations."""

import pytest

# Note: These tests require a running Qdrant instance
# Run with: docker-compose -f docker/docker-compose.dev.yml up -d qdrant


class TestQdrantIntegration:
    """Tests for Qdrant integration."""

    @pytest.mark.skip(reason="Requires running Qdrant instance")
    @pytest.mark.asyncio
    async def test_connection(self):
        """Test Qdrant connection."""
        from app.db import qdrant_manager

        await qdrant_manager.connect()
        health = await qdrant_manager.health_check()
        assert health["status"] == "healthy"
        await qdrant_manager.disconnect()

    @pytest.mark.skip(reason="Requires running Qdrant instance")
    @pytest.mark.asyncio
    async def test_collection_creation(self):
        """Test collection creation."""
        from app.db import qdrant_manager
        from app.core.config import settings

        await qdrant_manager.connect()
        await qdrant_manager.ensure_collection(
            collection_name="test_collection",
            vector_size=settings.EMBEDDING_DIMENSION,
        )
        health = await qdrant_manager.health_check()
        assert health["collections_count"] >= 1
        await qdrant_manager.disconnect()
