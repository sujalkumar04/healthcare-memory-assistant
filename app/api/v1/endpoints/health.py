"""Health check endpoint."""

from fastapi import APIRouter

from app.api.v1.schemas import HealthResponse
from app.db.qdrant_client import qdrant_manager

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health including Qdrant connection.",
)
async def health_check():
    """
    Health check endpoint.

    Returns:
    - status: overall health
    - qdrant: vector database status
    - version: API version
    """
    qdrant_health = await qdrant_manager.health_check()

    return HealthResponse(
        status="healthy" if qdrant_health["status"] == "healthy" else "degraded",
        qdrant=qdrant_health["status"],
        version="0.1.0",
    )


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if service is ready to handle requests.",
)
async def readiness_check():
    """Kubernetes readiness probe."""
    qdrant_health = await qdrant_manager.health_check()

    if qdrant_health["status"] != "healthy":
        return {"status": "not_ready", "reason": "Qdrant unavailable"}

    return {"status": "ready"}


@router.get(
    "/live",
    summary="Liveness check",
    description="Check if service is alive.",
)
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}
