"""Qdrant CRUD operations with patient isolation."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from qdrant_client.http import models

from app.db.collections import COLLECTION_NAME
from app.db.qdrant_client import qdrant_manager


class QdrantOperations:
    """
    CRUD operations for patient memories in Qdrant.
    
    IMPORTANT: All search operations MUST filter by patient_id
    to ensure patient data isolation.
    """

    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name

    # =========================================================================
    # CREATE / UPDATE
    # =========================================================================

    async def upsert_memory(
        self,
        vector: list[float],
        patient_id: str,
        content: str,
        memory_type: str = "note",
        source: str = "session",
        confidence: float = 1.0,
        modality: str = "text",
        metadata: dict[str, Any] | None = None,
        point_id: str | None = None,
    ) -> str:
        """
        Insert or update a memory in Qdrant.

        Args:
            vector: 384-dim embedding vector
            patient_id: REQUIRED - Patient identifier for isolation
            content: Memory content text
            memory_type: clinical | mental_health | medication | note
            source: session | doctor | import | pdf
            confidence: Confidence score (0.0 - 1.0)
            modality: Data modality (text | document | image)
            metadata: Additional JSON metadata
            point_id: Optional - existing point ID for updates

        Returns:
            Point ID of the upserted memory
        """
        memory_id = point_id or str(uuid4())
        
        payload = {
            "patient_id": patient_id,
            "content": content,
            "memory_type": memory_type,
            "source": source,
            "confidence": confidence,
            "modality": modality,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        qdrant_manager.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=memory_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        
        return memory_id

    # =========================================================================
    # READ / SEARCH
    # =========================================================================

    async def search_memory(
        self,
        query_vector: list[float],
        patient_id: str,
        limit: int = 10,
        min_score: float = 0.5,
        memory_types: list[str] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar memories with MANDATORY patient_id filter.

        Args:
            query_vector: 384-dim query embedding
            patient_id: REQUIRED - Patient ID filter (isolation)
            limit: Max results to return
            min_score: Minimum similarity score (0.0 - 1.0)
            memory_types: Optional filter by memory types
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            List of matching memories with scores
        """
        # Build filter conditions - patient_id is ALWAYS required
        must_conditions = [
            models.FieldCondition(
                key="patient_id",
                match=models.MatchValue(value=patient_id),
            )
        ]

        # Optional: filter by memory types
        if memory_types:
            must_conditions.append(
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchAny(any=memory_types),
                )
            )

        # Optional: date range filters
        if date_from:
            must_conditions.append(
                models.FieldCondition(
                    key="created_at",
                    range=models.Range(gte=date_from.isoformat()),
                )
            )
        if date_to:
            must_conditions.append(
                models.FieldCondition(
                    key="created_at",
                    range=models.Range(lte=date_to.isoformat()),
                )
            )

        # Execute search (qdrant-client 1.16.x uses query_points)
        try:
            results = qdrant_manager.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=models.Filter(must=must_conditions),
                limit=limit,
                # Note: score_threshold applied in Python for cloud compatibility
            ).points
        except Exception as e:
            # If query_points fails, return empty (no matches)
            print(f"Search error: {e}")
            return []

        # Apply score threshold in Python for better compatibility
        return [
            {
                "id": str(result.id),
                "score": result.score,
                **result.payload,
            }
            for result in results
            if result.score >= min_score
        ]

    async def get_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get all memories for a specific patient."""
        results, next_offset = qdrant_manager.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="patient_id",
                        match=models.MatchValue(value=patient_id),
                    )
                ]
            ),
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        memories = [
            {"id": str(point.id), **point.payload}
            for point in results
        ]

        return memories, len(memories)

    # =========================================================================
    # DELETE
    # =========================================================================

    async def delete_memory(self, point_id: str) -> bool:
        """Delete a single memory by point ID."""
        qdrant_manager.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[point_id]),
        )
        return True

    async def delete_patient_memories(self, patient_id: str) -> bool:
        """Delete ALL memories for a patient (use with caution)."""
        qdrant_manager.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="patient_id",
                            match=models.MatchValue(value=patient_id),
                        )
                    ]
                )
            ),
        )
        return True


# Singleton instance
qdrant_ops = QdrantOperations()
