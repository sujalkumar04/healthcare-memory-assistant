"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, memory, patient, search

api_router = APIRouter()

# Health check (no prefix needed)
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

# Memory ingestion
api_router.include_router(
    memory.router,
    prefix="/memory",
    tags=["Memory"],
)

# Search and retrieval
api_router.include_router(
    search.router,
    prefix="/search",
    tags=["Search"],
)

# Patient operations
api_router.include_router(
    patient.router,
    prefix="/patient",
    tags=["Patient"],
)
