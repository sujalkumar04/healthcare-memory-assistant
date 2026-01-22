"""Qdrant operations for image collection."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from qdrant_client.http import models

from app.db.collections import IMAGE_COLLECTION_NAME
from app.db.qdrant_client import qdrant_manager


class ImageOperations:
    """
    CRUD operations for patient images in Qdrant.
    
    Uses separate collection (patient_images) with 512-dim CLIP embeddings.
    IMPORTANT: All operations MUST filter by patient_id for isolation.
    """

    def __init__(self, collection_name: str = IMAGE_COLLECTION_NAME):
        self.collection_name = collection_name

    async def upsert_image(
        self,
        vector: list[float],
        patient_id: str,
        description: str = "",
        memory_type: str = "clinical",
        source: str = "upload",
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
        point_id: str | None = None,
    ) -> str:
        """
        Insert or update an image embedding in Qdrant.

        Args:
            vector: 512-dim CLIP embedding vector
            patient_id: REQUIRED - Patient identifier for isolation
            description: Optional description of image content
            memory_type: clinical | diagnostic | wound | other
            source: upload | import | device
            confidence: Confidence score (0.0 - 1.0)
            metadata: Additional JSON metadata (filename, dimensions, etc.)
            point_id: Optional - existing point ID for updates

        Returns:
            Point ID of the upserted image
        """
        image_id = point_id or str(uuid4())
        
        payload = {
            "patient_id": patient_id,
            "description": description,
            "memory_type": memory_type,
            "source": source,
            "confidence": confidence,
            "modality": "image",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        qdrant_manager.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=image_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        
        return image_id

    async def search_images(
        self,
        query_vector: list[float],
        patient_id: str,
        limit: int = 10,
        min_score: float = 0.5,
        memory_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar images with MANDATORY patient_id filter.

        Args:
            query_vector: 512-dim CLIP query embedding
            patient_id: REQUIRED - Patient ID filter (isolation)
            limit: Max results to return
            min_score: Minimum similarity score
            memory_types: Optional filter by image types

        Returns:
            List of matching images with scores
        """
        must_conditions = [
            models.FieldCondition(
                key="patient_id",
                match=models.MatchValue(value=patient_id),
            )
        ]

        if memory_types:
            must_conditions.append(
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchAny(any=memory_types),
                )
            )

        try:
            results = qdrant_manager.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=models.Filter(must=must_conditions),
                limit=limit,
            ).points
        except Exception as e:
            print(f"Image search error: {e}")
            return []

        return [
            {
                "id": str(result.id),
                "score": result.score,
                **result.payload,
            }
            for result in results
            if result.score >= min_score
        ]

    async def get_patient_images(
        self,
        patient_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get all images for a specific patient."""
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

        images = [
            {"id": str(point.id), **point.payload}
            for point in results
        ]

        return images, len(images)

    async def delete_image(self, point_id: str) -> bool:
        """Delete an image by point ID."""
        qdrant_manager.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[point_id]),
        )
        return True


# Singleton instance
image_ops = ImageOperations()
