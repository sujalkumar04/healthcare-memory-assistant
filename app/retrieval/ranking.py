"""Result ranking and reranking strategies."""

from typing import Any


async def rerank_results(
    query: str,
    results: list[dict[str, Any]],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """
    Rerank search results for better relevance.

    This is a placeholder for more sophisticated reranking.
    In production, consider using:
    - Cross-encoder models (e.g., sentence-transformers)
    - Cohere Rerank API
    - Custom relevance scoring

    Args:
        query: Original search query
        results: Initial search results
        top_k: Number of results to return

    Returns:
        Reranked results
    """
    # Simple reranking based on:
    # 1. Exact match boost
    # 2. Recency boost
    # 3. Memory type priority

    query_lower = query.lower()

    for result in results:
        score = result.get("score", 0.5)

        # Exact match boost
        content_lower = result.get("content", "").lower()
        if query_lower in content_lower:
            score += 0.1

        # Memory type priority (clinical > mental_health > others)
        memory_type = result.get("memory_type", "general")
        type_boosts = {
            "clinical": 0.05,
            "mental_health": 0.04,
            "medication": 0.03,
        }
        score += type_boosts.get(memory_type, 0)

        result["reranked_score"] = min(score, 1.0)

    # Sort by reranked score
    results.sort(key=lambda x: x.get("reranked_score", 0), reverse=True)

    return results[:top_k]


def calculate_relevance_score(
    semantic_score: float,
    recency_factor: float = 1.0,
    type_factor: float = 1.0,
) -> float:
    """Calculate combined relevance score."""
    return semantic_score * 0.7 + recency_factor * 0.2 + type_factor * 0.1
