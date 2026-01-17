"""Unit tests for retrieval module."""

import pytest
from app.retrieval.ranking import rerank_results, calculate_relevance_score


class TestRanking:
    """Tests for ranking utilities."""

    @pytest.mark.asyncio
    async def test_rerank_results_empty(self):
        """Test reranking with empty results."""
        results = await rerank_results("query", [], top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_rerank_results_preserves_order_for_equal_scores(self):
        """Test reranking preserves order for equal scores."""
        results = [
            {"content": "test 1", "score": 0.8, "memory_type": "general"},
            {"content": "test 2", "score": 0.8, "memory_type": "general"},
        ]
        reranked = await rerank_results("other", results, top_k=5)
        assert len(reranked) == 2

    def test_calculate_relevance_score(self):
        """Test relevance score calculation."""
        score = calculate_relevance_score(0.8, 1.0, 1.0)
        assert 0 <= score <= 1
        assert score == pytest.approx(0.86, rel=0.01)
