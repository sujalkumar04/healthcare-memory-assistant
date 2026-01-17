"""Patient endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import PatientSummaryResponse, SuggestionResponse
from app.retrieval import retrieval_engine
from app.reasoning import reasoning_chain
from app.db.operations import qdrant_ops

router = APIRouter()


@router.get(
    "/{patient_id}/summary",
    response_model=PatientSummaryResponse,
    summary="Get patient summary",
    description="Generate an evidence-grounded summary of patient records.",
)
async def get_patient_summary(patient_id: str):
    """
    Generate a summary of patient records.

    Flow:
    1. Retrieve recent memories for patient
    2. If NO memories: return empty summary
    3. If memories exist: generate grounded summary
    4. Return summary with disclaimer

    Summary is evidence-bound and will not hallucinate.
    """
    if not patient_id or not patient_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id is required",
        )

    try:
        # Get patient memories
        memories, total = await qdrant_ops.get_by_patient(
            patient_id=patient_id,
            limit=20,  # Top 20 for summary
        )

        # Filter active memories
        active_memories = [
            m for m in memories
            if m.get("metadata", {}).get("is_active", True)
        ]

        if not active_memories:
            return PatientSummaryResponse(
                patient_id=patient_id,
                summary="No records found for this patient.",
                memory_count=0,
                has_context=False,
                disclaimer="No patient records available.",
            )

        # Convert to evidence format
        evidence_dicts = [
            {
                "content": m.get("content", ""),
                "memory_type": m.get("memory_type", "note"),
                "source": m.get("source", "unknown"),
                "created_at": m.get("created_at", ""),
                "confidence": m.get("confidence", 1.0),
            }
            for m in active_memories
        ]

        # Generate summary using reasoning layer
        response = await reasoning_chain.summarize_records(
            patient_id=patient_id,
            evidence=evidence_dicts,
        )

        return PatientSummaryResponse(
            patient_id=patient_id,
            summary=response.answer_text,
            memory_count=len(active_memories),
            has_context=response.has_context,
            disclaimer=response.disclaimer,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}",
        )


@router.get(
    "/{patient_id}/stats",
    summary="Get patient memory statistics",
    description="Get memory counts and metadata for a patient.",
)
async def get_patient_stats(patient_id: str):
    """Get memory statistics for a patient."""
    if not patient_id or not patient_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id is required",
        )

    try:
        memories, total = await qdrant_ops.get_by_patient(
            patient_id=patient_id,
            limit=1000,
        )

        # Calculate stats
        type_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}
        active_count = 0

        for m in memories:
            # Count by type
            mem_type = m.get("memory_type", "unknown")
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

            # Count by source
            source = m.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

            # Count active
            if m.get("metadata", {}).get("is_active", True):
                active_count += 1

        return {
            "patient_id": patient_id,
            "total_memories": len(memories),
            "active_memories": active_count,
            "by_type": type_counts,
            "by_source": source_counts,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats retrieval failed: {str(e)}",
        )


@router.get(
    "/{patient_id}/suggestions",
    response_model=SuggestionResponse,
    summary="Get smart suggestions",
    description="Analyze patient records and suggest follow-up questions.",
)
async def get_patient_suggestions(patient_id: str):
    """
    Generate smart follow-up questions.
    
    Flow:
    1. Retrieve recent patient memories (Top 10)
    2. Analyze with LLM to find gaps
    3. detailed questions
    """
    if not patient_id or not patient_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id is required",
        )

    try:
        # Get recent memories for context
        memories, _ = await qdrant_ops.get_by_patient(
            patient_id=patient_id,
            limit=10, 
        )

        evidence_dicts = [
            {
                "content": m.get("content", ""),
                "memory_type": m.get("memory_type", "note"),
                "source": m.get("source", "unknown"),
                "created_at": m.get("created_at", ""),
            }
            for m in memories
        ]

        suggestions = await reasoning_chain.suggest_followup_questions(evidence_dicts)

        return SuggestionResponse(
            patient_id=patient_id,
            suggestions=suggestions,
            based_on_count=len(memories),
        )

    except Exception as e:
        # Fallback to generic suggestions if anything fails
        print(f"Suggestion error: {e}")
        return SuggestionResponse(
            patient_id=patient_id,
            suggestions=[
                "What are the patient's reported symptoms?",
                "Has there been any medication change?",
                "What is the latest diagnosis?"
            ],
            based_on_count=0,
        )

