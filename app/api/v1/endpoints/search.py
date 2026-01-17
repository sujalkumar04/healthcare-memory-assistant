"""Search and retrieval endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import (
    SearchRequest,
    SearchResponse,
    EvidenceItem,
    ContextSearchRequest,
    ContextSearchResponse,
)
from app.retrieval import retrieval_engine
from app.reasoning import reasoning_chain

router = APIRouter()


@router.post(
    "",
    response_model=SearchResponse,
    summary="Semantic memory search",
    description="Search patient memories using semantic similarity. No LLM usage.",
)
async def search_memories(request: SearchRequest):
    """
    Search for relevant memories using semantic similarity.

    Flow:
    1. Embed query (384-dim)
    2. Search Qdrant (filtered by patient_id)
    3. Rank by combined score (70% semantic + 30% confidence)
    4. Return structured evidence

    NOTE: This endpoint does NOT use LLM. For grounded answers, use /search/context.
    """
    try:
        evidence_list = await retrieval_engine.retrieve(
            patient_id=request.patient_id,
            query=request.query,
            limit=request.limit,
            memory_types=request.memory_types,
        )

        # Convert to response schema
        evidence_items = [
            EvidenceItem(
                content=e.content,
                semantic_score=e.semantic_score,
                confidence=e.confidence,
                combined_score=e.combined_score,
                source=e.source,
                memory_type=e.memory_type,
                created_at=e.created_at,
                point_id=e.point_id,
                parent_id=e.parent_id,
                chunk_index=e.chunk_index,
            )
            for e in evidence_list
        ]

        return SearchResponse(
            query=request.query,
            patient_id=request.patient_id,
            total_found=len(evidence_items),
            evidence=evidence_items,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post(
    "/context",
    response_model=ContextSearchResponse,
    summary="Search with grounded answer",
    description="Search memories and generate evidence-grounded answer using LLM.",
)
async def search_with_context(request: ContextSearchRequest):
    """
    Search memories and generate an LLM-grounded answer.

    Flow:
    1. Retrieve relevant evidence
    2. If NO evidence: return fixed response (NO LLM call)
    3. If evidence exists: call reasoning layer with evidence
    4. Return grounded answer with sources

    HALLUCINATION CONTROL: LLM only called if evidence exists.
    """
    try:
        # Step 1: Retrieve evidence
        evidence_list = await retrieval_engine.retrieve(
            patient_id=request.patient_id,
            query=request.query,
            limit=10,
            # Uses default min_score (0.2) from retrieval engine
        )

        # Step 2: Convert to dict for reasoning layer
        evidence_dicts = [e.to_dict() for e in evidence_list]

        # Step 3: Call reasoning (handles empty evidence internally)
        response = await reasoning_chain.reason(
            patient_id=request.patient_id,
            query=request.query,
            evidence=evidence_dicts,
            mode=request.mode,
        )

        return ContextSearchResponse(
            answer_text=response.answer_text,
            has_context=response.has_context,
            evidence_count=response.evidence_count,
            sources_used=response.sources_used,
            disclaimer=response.disclaimer,
            query=response.query,
            patient_id=response.patient_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context search failed: {str(e)}",
        )
