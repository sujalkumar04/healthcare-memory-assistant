"""
Retrieval Engine (Component 5) - Multimodal

Semantic search and ranking for patient memories across modalities.
Returns structured evidence without LLM reasoning.
"""

from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict, field

from app.db.operations import qdrant_ops
from app.db.image_operations import image_ops
from app.embedding import embedder


# =============================================================================
# RANKING WEIGHTS
# =============================================================================

# Combined score = (SEMANTIC_WEIGHT * semantic_score) + (CONFIDENCE_WEIGHT * confidence)
SEMANTIC_WEIGHT = 0.7
CONFIDENCE_WEIGHT = 0.3

# Default retrieval limits
DEFAULT_LIMIT = 10
MAX_LIMIT = 100
DEFAULT_MIN_SCORE = 0.2  # Lowered for demo data (tunable)

# Modality constants
MODALITY_TEXT = "text"
MODALITY_DOCUMENT = "document"
MODALITY_IMAGE = "image"
TEXT_MODALITIES = [MODALITY_TEXT, MODALITY_DOCUMENT]
ALL_MODALITIES = [MODALITY_TEXT, MODALITY_DOCUMENT, MODALITY_IMAGE]


@dataclass
class RetrievalEvidence:
    """
    Structured evidence object returned by retrieval.
    
    Contains all information needed for:
    - Display to user
    - LLM reasoning (in next component)
    - Audit and traceability
    
    For images: content contains description/reference, metadata has image details.
    For text/docs: content contains actual text chunk.
    """
    content: str  # Text content OR image description/reference
    semantic_score: float
    confidence: float
    combined_score: float
    source: str
    memory_type: str
    modality: str  # text | document | image
    created_at: str
    point_id: str
    # Chunk traceability (text/doc only)
    parent_id: str | None = None
    chunk_index: int | None = None
    total_chunks: int | None = None
    # Image-specific metadata
    image_filename: str | None = None
    image_width: int | None = None
    image_height: int | None = None
    # Extra metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def is_image(self) -> bool:
        """Check if this evidence is an image."""
        return self.modality == MODALITY_IMAGE


class RetrievalEngine:
    """
    Multimodal semantic retrieval engine for patient memories.
    
    Responsibilities:
    - Embed user queries (384-dim for text, 512-dim for images)
    - Search Qdrant with patient isolation
    - Filter by modality (text, document, image, or all)
    - Filter inactive (soft-deleted) memories
    - Rank by combined score (semantic + confidence)
    - Return structured evidence
    
    NOTE: This component does NOT:
    - Generate text (no LLM)
    - Implement API routes
    """

    # =========================================================================
    # MAIN RETRIEVAL (TEXT/DOCUMENT)
    # =========================================================================

    async def retrieve(
        self,
        patient_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
        min_score: float = DEFAULT_MIN_SCORE,
        memory_types: list[str] | None = None,
        modalities: list[str] | None = None,
        include_inactive: bool = False,
    ) -> list[RetrievalEvidence]:
        """
        Retrieve relevant memories for a patient query.

        Pipeline:
        1. Embed query (384-dim)
        2. Search Qdrant (filtered by patient_id, optional modality filter)
        3. Filter inactive memories
        4. Calculate combined scores
        5. Rank and return evidence

        Args:
            patient_id: REQUIRED - Patient identifier (isolation key)
            query: User query text
            limit: Max results (default: 10, max: 100)
            min_score: Minimum semantic score threshold
            memory_types: Filter by types (clinical, mental_health, etc.)
            modalities: Filter by modalities (text, document). For images, use retrieve_images().
            include_inactive: Include soft-deleted memories (default: False)

        Returns:
            List of RetrievalEvidence, ranked by combined_score

        Raises:
            ValueError: If patient_id is missing
        """
        # Validate inputs
        if not patient_id:
            raise ValueError("patient_id is required for retrieval")
        if not query or not query.strip():
            return []  # Empty query = empty results (no hallucination)
        
        # Enforce limits
        limit = min(limit, MAX_LIMIT)

        # Step 1: Embed query
        query_vector = embedder.embed_text(query.strip())

        # Step 2: Search Qdrant (with patient isolation)
        raw_results = await qdrant_ops.search_memory(
            query_vector=query_vector,
            patient_id=patient_id,  # MANDATORY patient filter
            limit=limit * 2,  # Fetch extra for filtering
            min_score=min_score,
            memory_types=memory_types,
        )

        # Step 3: Filter by modality (if specified)
        if modalities:
            raw_results = [
                r for r in raw_results
                if r.get("modality", "text") in modalities
            ]

        # Step 4: Filter inactive memories
        if not include_inactive:
            raw_results = [
                r for r in raw_results
                if r.get("metadata", {}).get("is_active", True)
            ]

        # Step 5 & 6: Calculate combined scores and build evidence
        evidence_list = []
        for result in raw_results:
            evidence = self._build_text_evidence(result)
            evidence_list.append(evidence)

        # Sort by combined score (descending)
        evidence_list.sort(key=lambda e: e.combined_score, reverse=True)

        # Return top N
        return evidence_list[:limit]

    # =========================================================================
    # IMAGE RETRIEVAL
    # =========================================================================

    async def retrieve_images(
        self,
        patient_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
        min_score: float = DEFAULT_MIN_SCORE,
        memory_types: list[str] | None = None,
    ) -> list[RetrievalEvidence]:
        """
        Retrieve relevant images for a patient query.

        Uses CLIP text encoder to embed query, then searches image collection.

        Args:
            patient_id: REQUIRED - Patient identifier
            query: User query text
            limit: Max results
            min_score: Minimum similarity threshold
            memory_types: Filter by types

        Returns:
            List of RetrievalEvidence (image references)
        """
        if not patient_id:
            raise ValueError("patient_id is required for retrieval")
        if not query or not query.strip():
            return []

        limit = min(limit, MAX_LIMIT)

        # Embed query using CLIP text encoder
        try:
            from app.multimodal.image import image_processor
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            # Load CLIP model for text encoding
            model_name = "openai/clip-vit-base-patch32"
            processor = CLIPProcessor.from_pretrained(model_name)
            model = CLIPModel.from_pretrained(model_name)
            model.eval()
            
            # Encode query text
            inputs = processor(text=[query.strip()], return_tensors="pt", padding=True)
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                query_vector = text_features.squeeze().tolist()
            
        except ImportError:
            # If CLIP not available, return empty (no image search)
            return []

        # Search image collection
        raw_results = await image_ops.search_images(
            query_vector=query_vector,
            patient_id=patient_id,
            limit=limit,
            min_score=min_score,
            memory_types=memory_types,
        )

        # Build image evidence
        evidence_list = []
        for result in raw_results:
            evidence = self._build_image_evidence(result)
            evidence_list.append(evidence)

        evidence_list.sort(key=lambda e: e.combined_score, reverse=True)
        return evidence_list[:limit]

    # =========================================================================
    # MULTIMODAL RETRIEVAL
    # =========================================================================

    async def retrieve_multimodal(
        self,
        patient_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
        min_score: float = DEFAULT_MIN_SCORE,
        modalities: list[str] | None = None,
        memory_types: list[str] | None = None,
        include_inactive: bool = False,
    ) -> list[RetrievalEvidence]:
        """
        Retrieve evidence across all modalities (text, document, image).

        Queries both text/document collection and image collection,
        then merges and ranks results.

        Args:
            patient_id: REQUIRED - Patient identifier
            query: User query text
            limit: Max total results
            min_score: Minimum similarity threshold
            modalities: Filter by modalities (text, document, image). None = all.
            memory_types: Filter by types
            include_inactive: Include soft-deleted

        Returns:
            Combined and ranked list of RetrievalEvidence
        """
        if not patient_id:
            raise ValueError("patient_id is required for retrieval")
        if not query or not query.strip():
            return []

        # Determine which modalities to query
        query_modalities = modalities or ALL_MODALITIES
        
        all_evidence: list[RetrievalEvidence] = []

        # Query text/document memories
        text_modalities = [m for m in query_modalities if m in TEXT_MODALITIES]
        if text_modalities:
            text_evidence = await self.retrieve(
                patient_id=patient_id,
                query=query,
                limit=limit,
                min_score=min_score,
                memory_types=memory_types,
                modalities=text_modalities,
                include_inactive=include_inactive,
            )
            all_evidence.extend(text_evidence)

        # Query images
        if MODALITY_IMAGE in query_modalities:
            image_evidence = await self.retrieve_images(
                patient_id=patient_id,
                query=query,
                limit=limit,
                min_score=min_score,
                memory_types=memory_types,
            )
            all_evidence.extend(image_evidence)

        # Sort all by combined score
        all_evidence.sort(key=lambda e: e.combined_score, reverse=True)

        return all_evidence[:limit]

    # =========================================================================
    # EVIDENCE BUILDERS
    # =========================================================================

    def _build_text_evidence(self, result: dict[str, Any]) -> RetrievalEvidence:
        """
        Build structured evidence from text/document Qdrant result.
        
        Combined Score Formula:
        combined = 0.7 * semantic_score + 0.3 * confidence
        """
        semantic_score = result.get("score", 0.0)
        confidence = result.get("confidence", 1.0)
        
        combined_score = (
            SEMANTIC_WEIGHT * semantic_score +
            CONFIDENCE_WEIGHT * confidence
        )
        
        metadata = result.get("metadata", {})
        
        return RetrievalEvidence(
            content=result.get("content", ""),
            semantic_score=round(semantic_score, 4),
            confidence=round(confidence, 4),
            combined_score=round(combined_score, 4),
            source=result.get("source", "unknown"),
            memory_type=result.get("memory_type", "note"),
            modality=result.get("modality", "text"),
            created_at=result.get("created_at", ""),
            point_id=result.get("id", ""),
            # Chunk traceability
            parent_id=metadata.get("parent_id"),
            chunk_index=metadata.get("chunk_index"),
            total_chunks=metadata.get("total_chunks"),
            # Full metadata
            metadata=metadata,
        )

    def _build_image_evidence(self, result: dict[str, Any]) -> RetrievalEvidence:
        """
        Build structured evidence from image Qdrant result.
        
        Images return metadata reference, not full content.
        """
        semantic_score = result.get("score", 0.0)
        confidence = result.get("confidence", 1.0)
        
        combined_score = (
            SEMANTIC_WEIGHT * semantic_score +
            CONFIDENCE_WEIGHT * confidence
        )
        
        metadata = result.get("metadata", {})
        
        # Build content as image reference
        filename = metadata.get("original_filename", "image")
        description = result.get("description", "")
        content = f"[IMAGE: {filename}]"
        if description:
            content += f" {description}"
        
        return RetrievalEvidence(
            content=content,
            semantic_score=round(semantic_score, 4),
            confidence=round(confidence, 4),
            combined_score=round(combined_score, 4),
            source=result.get("source", "upload"),
            memory_type=result.get("memory_type", "clinical"),
            modality="image",
            created_at=result.get("created_at", ""),
            point_id=result.get("id", ""),
            # Image-specific
            image_filename=metadata.get("original_filename"),
            image_width=metadata.get("width"),
            image_height=metadata.get("height"),
            # Full metadata
            metadata=metadata,
        )

    # =========================================================================
    # CONTEXT RETRIEVAL (for LLM)
    # =========================================================================

    async def get_context(
        self,
        patient_id: str,
        query: str,
        max_tokens: int = 2000,
        limit: int = 10,
        include_images: bool = False,
    ) -> str:
        """
        Get concatenated context string for LLM prompting.
        
        Returns empty string if no relevant memories found.
        (HALLUCINATION CONTROL: empty context = no generation)
        
        Args:
            patient_id: Patient identifier
            query: Query text
            max_tokens: Approximate max tokens (4 chars ≈ 1 token)
            limit: Max memories to consider
            include_images: Include image references in context
            
        Returns:
            Concatenated context string or empty string
        """
        if include_images:
            evidence = await self.retrieve_multimodal(
                patient_id=patient_id,
                query=query,
                limit=limit,
                min_score=0.5,
            )
        else:
            evidence = await self.retrieve(
                patient_id=patient_id,
                query=query,
                limit=limit,
                min_score=0.6,  # Higher threshold for context
            )
        
        if not evidence:
            return ""  # No context = no hallucination
        
        # Build context with token budget
        context_parts = []
        current_chars = 0
        max_chars = max_tokens * 4  # Rough estimate
        
        for e in evidence:
            content_chars = len(e.content)
            if current_chars + content_chars > max_chars:
                break
            
            # Format each memory with modality indicator
            modality_tag = f"[{e.modality.upper()}]" if e.modality != "text" else ""
            formatted = (
                f"[{e.memory_type.upper()}]{modality_tag} ({e.source}, {e.created_at[:10]})\n"
                f"{e.content}"
            )
            context_parts.append(formatted)
            current_chars += content_chars
        
        return "\n\n---\n\n".join(context_parts)

    # =========================================================================
    # RETRIEVAL STATS
    # =========================================================================

    async def retrieve_with_stats(
        self,
        patient_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
        modalities: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve with additional statistics.
        
        Useful for debugging and explaining retrieval results.
        
        Returns:
            {
                "query": str,
                "patient_id": str,
                "total_found": int,
                "modalities_queried": [...],
                "avg_semantic_score": float,
                "avg_confidence": float,
                "evidence": [...]
            }
        """
        if modalities and MODALITY_IMAGE in modalities:
            evidence = await self.retrieve_multimodal(
                patient_id=patient_id,
                query=query,
                limit=limit,
                modalities=modalities,
            )
        else:
            evidence = await self.retrieve(
                patient_id=patient_id,
                query=query,
                limit=limit,
                modalities=modalities,
            )
        
        if not evidence:
            return {
                "query": query,
                "patient_id": patient_id,
                "total_found": 0,
                "modalities_queried": modalities or ALL_MODALITIES,
                "avg_semantic_score": 0.0,
                "avg_confidence": 0.0,
                "evidence": [],
            }
        
        avg_semantic = sum(e.semantic_score for e in evidence) / len(evidence)
        avg_confidence = sum(e.confidence for e in evidence) / len(evidence)
        modalities_found = list(set(e.modality for e in evidence))
        
        return {
            "query": query,
            "patient_id": patient_id,
            "total_found": len(evidence),
            "modalities_queried": modalities or ALL_MODALITIES,
            "modalities_found": modalities_found,
            "avg_semantic_score": round(avg_semantic, 4),
            "avg_confidence": round(avg_confidence, 4),
            "evidence": [e.to_dict() for e in evidence],
        }


# Singleton instance
retrieval_engine = RetrievalEngine()

