"""
Retrieval Engine (Component 5)

Semantic search and ranking for patient memories.
Returns structured evidence without LLM reasoning.
"""

from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict

from app.db.operations import qdrant_ops
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


@dataclass
class RetrievalEvidence:
    """
    Structured evidence object returned by retrieval.
    
    Contains all information needed for:
    - Display to user
    - LLM reasoning (in next component)
    - Audit and traceability
    """
    content: str
    semantic_score: float
    confidence: float
    combined_score: float
    source: str
    memory_type: str
    created_at: str
    point_id: str
    # Chunk traceability
    parent_id: str | None = None
    chunk_index: int | None = None
    total_chunks: int | None = None
    # Extra metadata
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class RetrievalEngine:
    """
    Semantic retrieval engine for patient memories.
    
    Responsibilities:
    - Embed user queries (384-dim)
    - Search Qdrant with patient isolation
    - Filter inactive (soft-deleted) memories
    - Rank by combined score (semantic + confidence)
    - Return structured evidence
    
    NOTE: This component does NOT:
    - Generate text (no LLM)
    - Implement API routes
    """

    # =========================================================================
    # MAIN RETRIEVAL
    # =========================================================================

    async def retrieve(
        self,
        patient_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
        min_score: float = DEFAULT_MIN_SCORE,
        memory_types: list[str] | None = None,
        include_inactive: bool = False,
    ) -> list[RetrievalEvidence]:
        """
        Retrieve relevant memories for a patient query.

        Pipeline:
        1. Embed query (384-dim)
        2. Search Qdrant (filtered by patient_id)
        3. Filter inactive memories
        4. Calculate combined scores
        5. Rank and return evidence

        Args:
            patient_id: REQUIRED - Patient identifier (isolation key)
            query: User query text
            limit: Max results (default: 10, max: 100)
            min_score: Minimum semantic score threshold
            memory_types: Filter by types (clinical, mental_health, etc.)
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

        # Step 3: Filter inactive memories
        if not include_inactive:
            raw_results = [
                r for r in raw_results
                if r.get("metadata", {}).get("is_active", True)
            ]

        # Step 4 & 5: Calculate combined scores and build evidence
        evidence_list = []
        for result in raw_results:
            evidence = self._build_evidence(result)
            evidence_list.append(evidence)

        # Sort by combined score (descending)
        evidence_list.sort(key=lambda e: e.combined_score, reverse=True)

        # Return top N
        return evidence_list[:limit]

    def _build_evidence(self, result: dict[str, Any]) -> RetrievalEvidence:
        """
        Build structured evidence from Qdrant result.
        
        Combined Score Formula:
        combined = 0.7 * semantic_score + 0.3 * confidence
        
        This weights semantic relevance higher (70%) while
        still considering memory reliability (30%).
        """
        semantic_score = result.get("score", 0.0)
        confidence = result.get("confidence", 1.0)
        
        # Calculate combined score
        combined_score = (
            SEMANTIC_WEIGHT * semantic_score +
            CONFIDENCE_WEIGHT * confidence
        )
        
        # Extract metadata
        metadata = result.get("metadata", {})
        
        return RetrievalEvidence(
            content=result.get("content", ""),
            semantic_score=round(semantic_score, 4),
            confidence=round(confidence, 4),
            combined_score=round(combined_score, 4),
            source=result.get("source", "unknown"),
            memory_type=result.get("memory_type", "note"),
            created_at=result.get("created_at", ""),
            point_id=result.get("id", ""),
            # Chunk traceability
            parent_id=metadata.get("parent_id"),
            chunk_index=metadata.get("chunk_index"),
            total_chunks=metadata.get("total_chunks"),
            # Full metadata for advanced use
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
            
        Returns:
            Concatenated context string or empty string
        """
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
            
            # Format each memory with metadata
            formatted = (
                f"[{e.memory_type.upper()}] ({e.source}, {e.created_at[:10]})\n"
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
    ) -> dict[str, Any]:
        """
        Retrieve with additional statistics.
        
        Useful for debugging and explaining retrieval results.
        
        Returns:
            {
                "query": str,
                "patient_id": str,
                "total_found": int,
                "avg_semantic_score": float,
                "avg_confidence": float,
                "evidence": [...]
            }
        """
        evidence = await self.retrieve(
            patient_id=patient_id,
            query=query,
            limit=limit,
        )
        
        if not evidence:
            return {
                "query": query,
                "patient_id": patient_id,
                "total_found": 0,
                "avg_semantic_score": 0.0,
                "avg_confidence": 0.0,
                "evidence": [],
            }
        
        avg_semantic = sum(e.semantic_score for e in evidence) / len(evidence)
        avg_confidence = sum(e.confidence for e in evidence) / len(evidence)
        
        return {
            "query": query,
            "patient_id": patient_id,
            "total_found": len(evidence),
            "avg_semantic_score": round(avg_semantic, 4),
            "avg_confidence": round(avg_confidence, 4),
            "evidence": [e.to_dict() for e in evidence],
        }


# Singleton instance
retrieval_engine = RetrievalEngine()
