"""Memory ingestion endpoint."""

from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import MemoryIngestRequest, MemoryIngestResponse
from app.memory.manager import memory_manager

router = APIRouter()


@router.post(
    "",
    response_model=MemoryIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new memory",
    description="Ingest patient memory with automatic chunking and embedding.",
)
async def ingest_memory(request: MemoryIngestRequest):
    """
    Ingest a new memory for a patient.

    Pipeline:
    1. Validate patient_id presence
    2. Preprocess and chunk text
    3. Embed each chunk
    4. Store with patient isolation

    If similar memory exists, it will be reinforced instead of duplicated.
    """
    try:
        # Consolidate metadata
        meta = request.metadata or {}
        if request.profile:
            meta["patient_profile"] = request.profile.model_dump(exclude_none=True)
        if request.visit:
            meta["visit"] = request.visit.model_dump(exclude_none=True)

        result = await memory_manager.ingest_memory(
            patient_id=request.patient_id,
            raw_text=request.raw_text,
            memory_type=request.memory_type,
            source=request.source,
            metadata=meta,
            check_reinforcement=True,
        )

        return MemoryIngestResponse(
            action=result["action"],
            point_ids=result["point_ids"],
            chunks_stored=len(result["point_ids"]),
            patient_id=request.patient_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )
