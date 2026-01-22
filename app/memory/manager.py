"""
Evolving Memory Management (Component 4)

Handles memory lifecycle: ingestion, reinforcement, decay, and soft delete.
Retrieval/search is implemented separately in the retrieval component.
"""

from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4
import math

from app.db.operations import qdrant_ops
from app.embedding import embedder, preprocessor, chunker


# =============================================================================
# CONFIDENCE MODEL CONSTANTS
# =============================================================================

# Initial confidence for new memories
INITIAL_CONFIDENCE = 1.0

# Minimum confidence (never decay below this)
MIN_CONFIDENCE = 0.1

# Maximum confidence (cap after reinforcement)
MAX_CONFIDENCE = 1.0

# Reinforcement boost when similar memory is detected
REINFORCEMENT_BOOST = 0.15

# Similarity threshold to trigger reinforcement (0.0 - 1.0)
SIMILARITY_THRESHOLD = 0.85

# Decay settings
DECAY_HALF_LIFE_DAYS = 90  # Confidence halves every 90 days if unused
DECAY_GRACE_PERIOD_DAYS = 7  # No decay for first 7 days


class MemoryConfidenceModel:
    """
    Memory confidence scoring model.
    
    Confidence Behavior:
    - New memory: starts at 1.0
    - Reinforcement: +0.15 when similar memory detected (capped at 1.0)
    - Decay: halves every 90 days if unused (minimum 0.1)
    
    This models human memory where:
    - Repeated information is remembered better
    - Unused memories fade over time
    - Nothing is completely forgotten (audit trail)
    """

    @staticmethod
    def calculate_decay(
        original_confidence: float,
        created_at: datetime,
        last_accessed: datetime | None = None,
    ) -> float:
        """
        Calculate decayed confidence based on time elapsed.
        
        Formula: confidence * (0.5 ^ (days / half_life))
        
        Args:
            original_confidence: Original confidence score
            created_at: When memory was created
            last_accessed: Last access time (uses created_at if None)
            
        Returns:
            Decayed confidence (never below MIN_CONFIDENCE)
        """
        reference_time = last_accessed or created_at
        now = datetime.now(timezone.utc)
        
        # Ensure timezone awareness
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)
        
        days_elapsed = (now - reference_time).days
        
        # Grace period: no decay for recent memories
        if days_elapsed <= DECAY_GRACE_PERIOD_DAYS:
            return original_confidence
        
        # Exponential decay with half-life
        effective_days = days_elapsed - DECAY_GRACE_PERIOD_DAYS
        decay_factor = math.pow(0.5, effective_days / DECAY_HALF_LIFE_DAYS)
        
        decayed = original_confidence * decay_factor
        
        # Never drop below minimum
        return max(decayed, MIN_CONFIDENCE)

    @staticmethod
    def apply_reinforcement(current_confidence: float) -> float:
        """
        Apply reinforcement boost to confidence.
        
        Called when a similar memory is detected.
        Adds REINFORCEMENT_BOOST, capped at MAX_CONFIDENCE.
        
        Args:
            current_confidence: Current confidence score
            
        Returns:
            Reinforced confidence (capped at 1.0)
        """
        reinforced = current_confidence + REINFORCEMENT_BOOST
        return min(reinforced, MAX_CONFIDENCE)


class MemoryManager:
    """
    Evolving Memory Manager.
    
    Responsibilities:
    - Ingest new memories with confidence scoring
    - Reinforce similar existing memories
    - Apply time-based decay
    - Update and soft-delete memories
    - Enforce patient isolation on ALL operations
    
    NOTE: Search/retrieval is handled by the retrieval component.
    """

    def __init__(self):
        self.confidence_model = MemoryConfidenceModel()

    # =========================================================================
    # INGESTION WITH REINFORCEMENT
    # =========================================================================

    async def ingest_memory(
        self,
        patient_id: str,
        raw_text: str,
        memory_type: str = "note",
        source: str = "session",
        modality: str = "text",
        metadata: dict[str, Any] | None = None,
        check_reinforcement: bool = True,
    ) -> dict[str, Any]:
        """
        Ingest a memory with optional reinforcement detection.

        Pipeline:
        1. Preprocess and embed the new memory
        2. If check_reinforcement: look for similar existing memories
        3. If similar found: reinforce existing instead of creating new
        4. Otherwise: create new memory chunks

        Args:
            patient_id: REQUIRED - Patient identifier (isolation key)
            raw_text: Raw memory text to ingest
            memory_type: clinical | mental_health | medication | note
            source: session | doctor | import | pdf
            modality: Data modality (text | document | image)
            metadata: Additional JSON metadata
            check_reinforcement: Whether to check for similar memories

        Returns:
            {
                "action": "created" | "reinforced",
                "point_ids": [...],  # Created or reinforced point IDs
                "reinforced_count": int,  # Number of memories reinforced
            }
        """
        if not patient_id:
            raise ValueError("patient_id is required")
        if not raw_text or not raw_text.strip():
            raise ValueError("raw_text cannot be empty")

        # Generate parent document ID for chunk traceability
        parent_id = str(uuid4())

        # Preprocess
        processed_text = preprocessor.process(raw_text)
        
        # For reinforcement check, embed the full text first
        if check_reinforcement:
            full_embedding = embedder.embed_text(processed_text)
            
            # Check for similar existing memories
            similar = await self._find_similar_memories(
                patient_id=patient_id,
                query_vector=full_embedding,
                threshold=SIMILARITY_THRESHOLD,
            )
            
            if similar:
                # Reinforce existing memories instead of creating new
                reinforced_ids = await self._reinforce_memories(similar)
                return {
                    "action": "reinforced",
                    "point_ids": reinforced_ids,
                    "reinforced_count": len(reinforced_ids),
                }

        # No similar found or reinforcement disabled: create new
        chunks = chunker.chunk_text(processed_text)
        if not chunks:
            chunks = [processed_text]

        point_ids: list[str] = []
        
        for chunk_index, chunk_text in enumerate(chunks):
            vector = embedder.embed_text(chunk_text)
            point_id = str(uuid4())
            
            chunk_metadata = {
                **(metadata or {}),
                "parent_id": parent_id,
                "chunk_index": chunk_index,
                "total_chunks": len(chunks),
                "original_length": len(raw_text),
                "is_active": True,  # For soft delete
                "last_accessed": datetime.now(timezone.utc).isoformat(),
            }
            
            await qdrant_ops.upsert_memory(
                vector=vector,
                patient_id=patient_id,
                content=chunk_text,
                memory_type=memory_type,
                source=source,
                confidence=INITIAL_CONFIDENCE,
                modality=modality,
                metadata=chunk_metadata,
                point_id=point_id,
            )
            
            point_ids.append(point_id)

        return {
            "action": "created",
            "point_ids": point_ids,
            "reinforced_count": 0,
        }

    async def _find_similar_memories(
        self,
        patient_id: str,
        query_vector: list[float],
        threshold: float = SIMILARITY_THRESHOLD,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find semantically similar memories for a patient.
        
        PATIENT ISOLATION: Only searches within patient_id.
        
        Args:
            patient_id: Patient identifier
            query_vector: Query embedding
            threshold: Similarity threshold
            limit: Max results
            
        Returns:
            List of similar memories above threshold
        """
        # Use Qdrant search with patient filter
        results = await qdrant_ops.search_memory(
            query_vector=query_vector,
            patient_id=patient_id,  # MANDATORY patient isolation
            limit=limit,
            min_score=threshold,
        )
        
        # Filter to only active memories
        return [r for r in results if r.get("metadata", {}).get("is_active", True)]

    async def _reinforce_memories(
        self,
        memories: list[dict[str, Any]],
    ) -> list[str]:
        """
        Reinforce existing memories by boosting confidence.
        
        Args:
            memories: List of similar memories to reinforce
            
        Returns:
            List of reinforced point IDs
        """
        reinforced_ids = []
        
        for memory in memories:
            point_id = memory["id"]
            current_confidence = memory.get("confidence", INITIAL_CONFIDENCE)
            
            # Apply reinforcement boost
            new_confidence = self.confidence_model.apply_reinforcement(current_confidence)
            
            # Update metadata
            new_metadata = memory.get("metadata", {}).copy()
            new_metadata["last_reinforced"] = datetime.now(timezone.utc).isoformat()
            new_metadata["reinforcement_count"] = new_metadata.get("reinforcement_count", 0) + 1
            
            # Update in Qdrant
            await self.update_memory(
                point_id=point_id,
                patient_id=memory["patient_id"],  # Required for safety
                updates={
                    "confidence": new_confidence,
                    "metadata": new_metadata,
                },
            )
            
            reinforced_ids.append(point_id)
        
        return reinforced_ids

    # =========================================================================
    # DECAY OPERATIONS
    # =========================================================================

    async def apply_decay_to_patient(
        self,
        patient_id: str,
        batch_size: int = 100,
    ) -> dict[str, int]:
        """
        Apply time-based decay to all memories for a patient.
        
        Should be run periodically (e.g., daily cron job).
        
        PATIENT ISOLATION: Only affects specified patient.
        
        Args:
            patient_id: Patient identifier
            batch_size: Batch size for processing
            
        Returns:
            {"processed": int, "decayed": int}
        """
        memories, _ = await qdrant_ops.get_by_patient(
            patient_id=patient_id,
            limit=batch_size,
        )
        
        processed = 0
        decayed = 0
        
        for memory in memories:
            # Skip inactive memories
            if not memory.get("metadata", {}).get("is_active", True):
                continue
                
            created_at_str = memory.get("created_at")
            if not created_at_str:
                continue
                
            created_at = datetime.fromisoformat(created_at_str)
            current_confidence = memory.get("confidence", INITIAL_CONFIDENCE)
            
            # Calculate decayed confidence
            new_confidence = self.confidence_model.calculate_decay(
                original_confidence=current_confidence,
                created_at=created_at,
                last_accessed=self._parse_last_accessed(memory),
            )
            
            # Only update if confidence changed significantly
            if abs(new_confidence - current_confidence) > 0.01:
                await self.update_memory(
                    point_id=memory["id"],
                    patient_id=patient_id,
                    updates={"confidence": new_confidence},
                )
                decayed += 1
            
            processed += 1
        
        return {"processed": processed, "decayed": decayed}

    def _parse_last_accessed(self, memory: dict) -> datetime | None:
        """Parse last_accessed from memory metadata."""
        last_accessed_str = memory.get("metadata", {}).get("last_accessed")
        if last_accessed_str:
            return datetime.fromisoformat(last_accessed_str)
        return None

    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================

    async def update_memory(
        self,
        point_id: str,
        patient_id: str,
        updates: dict[str, Any],
    ) -> bool:
        """
        Update a memory's payload fields.
        
        SAFETY: Requires patient_id to prevent cross-patient updates.
        
        Args:
            point_id: Memory point ID
            patient_id: REQUIRED - Patient ID (for verification)
            updates: Fields to update (confidence, metadata, etc.)
            
        Returns:
            True if updated successfully
            
        Raises:
            ValueError: If patient_id doesn't match
        """
        # SAFETY: Verify patient ownership before update
        # This prevents cross-patient data modification
        existing = await self._get_memory_by_id(point_id)
        
        if not existing:
            raise ValueError(f"Memory {point_id} not found")
        
        if existing.get("patient_id") != patient_id:
            raise ValueError(
                f"Patient ID mismatch. Memory belongs to different patient. "
                f"Cross-patient updates are forbidden."
            )
        
        # Merge updates with existing payload
        updated_payload = {**existing, **updates}
        updated_payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Re-upsert with same vector (payload update only)
        # Note: We need to retrieve the vector for re-upserting
        # For efficiency, we use Qdrant's set_payload instead
        from qdrant_client.http import models
        from app.db.qdrant_client import qdrant_manager
        from app.db.collections import COLLECTION_NAME
        
        qdrant_manager.client.set_payload(
            collection_name=COLLECTION_NAME,
            payload=updates,
            points=[point_id],
        )
        
        return True

    async def _get_memory_by_id(self, point_id: str) -> dict[str, Any] | None:
        """Retrieve a memory by its point ID."""
        from qdrant_client.http import models
        from app.db.qdrant_client import qdrant_manager
        from app.db.collections import COLLECTION_NAME
        
        try:
            results = qdrant_manager.client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=[point_id],
                with_payload=True,
            )
            if results:
                return {"id": point_id, **results[0].payload}
            return None
        except Exception:
            return None

    # =========================================================================
    # DELETE OPERATIONS
    # =========================================================================

    async def soft_delete_memory(
        self,
        point_id: str,
        patient_id: str,
        reason: str = "user_requested",
    ) -> bool:
        """
        Soft delete a memory (mark as inactive, preserve for audit).
        
        SAFETY: Requires patient_id to prevent cross-patient deletes.
        
        Soft delete behavior:
        - Sets is_active = False
        - Preserves all data for audit trail
        - Memory excluded from searches (handled by retrieval layer)
        
        Args:
            point_id: Memory point ID
            patient_id: REQUIRED - Patient ID (for verification)
            reason: Deletion reason for audit
            
        Returns:
            True if soft-deleted successfully
        """
        await self.update_memory(
            point_id=point_id,
            patient_id=patient_id,
            updates={
                "metadata": {
                    "is_active": False,
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "deletion_reason": reason,
                },
            },
        )
        return True

    async def hard_delete_memory(
        self,
        point_id: str,
        patient_id: str,
    ) -> bool:
        """
        Permanently delete a memory (use with caution).
        
        SAFETY: Requires patient_id verification.
        
        WARNING: This is irreversible. Prefer soft_delete_memory.
        
        Args:
            point_id: Memory point ID
            patient_id: REQUIRED - Patient ID (for verification)
            
        Returns:
            True if deleted
        """
        # Verify patient ownership first
        existing = await self._get_memory_by_id(point_id)
        
        if not existing:
            raise ValueError(f"Memory {point_id} not found")
        
        if existing.get("patient_id") != patient_id:
            raise ValueError("Cross-patient deletion forbidden")
        
        return await qdrant_ops.delete_memory(point_id)

    # =========================================================================
    # AUDIO INGESTION
    # =========================================================================

    async def ingest_audio(
        self,
        patient_id: str,
        audio_bytes: bytes,
        filename: str,
        memory_type: str = "session",
        source: str = "recording",
        metadata: dict[str, Any] | None = None,
        check_reinforcement: bool = True,
    ) -> dict[str, Any]:
        """
        Ingest audio memory via transcription.

        Pipeline:
        1. Validate audio file
        2. Transcribe using Groq Whisper API
        3. Process transcribed text through standard ingestion
        4. Store with modality: "audio"

        Args:
            patient_id: REQUIRED - Patient identifier
            audio_bytes: Raw audio file bytes
            filename: Original filename (for format detection)
            memory_type: clinical | mental_health | medication | session
            source: recording | voicemail | session
            metadata: Additional JSON metadata
            check_reinforcement: Whether to check for similar memories

        Returns:
            {
                "action": "created" | "reinforced",
                "point_ids": [...],
                "transcript": str,
                "duration_seconds": float | None,
            }
        """
        from app.multimodal.audio import audio_processor

        if not patient_id:
            raise ValueError("patient_id is required")
        if not audio_bytes:
            raise ValueError("audio_bytes cannot be empty")

        # Step 1 & 2: Transcribe audio
        result = await audio_processor.transcribe_audio_bytes(
            audio_bytes=audio_bytes,
            filename=filename,
        )

        if not result.success:
            raise ValueError(f"Audio transcription failed: {result.error}")

        if not result.transcript or not result.transcript.strip():
            raise ValueError("Transcription returned empty text")

        # Step 3: Build audio-specific metadata
        audio_metadata = {
            **(metadata or {}),
            "original_filename": filename,
            "duration_seconds": result.duration_seconds,
            "transcription_model": "whisper-large-v3-turbo",
            "detected_language": result.language,
        }

        # Step 4: Process through standard ingestion with modality="audio"
        ingestion_result = await self.ingest_memory(
            patient_id=patient_id,
            raw_text=result.transcript,
            memory_type=memory_type,
            source=source,
            modality="audio",
            metadata=audio_metadata,
            check_reinforcement=check_reinforcement,
        )

        # Add transcript preview to result
        ingestion_result["transcript"] = result.transcript[:500] + ("..." if len(result.transcript) > 500 else "")
        ingestion_result["duration_seconds"] = result.duration_seconds

        return ingestion_result


# Singleton instance
memory_manager = MemoryManager()
