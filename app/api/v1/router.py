"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import audio, document, health, image, memory, patient, search

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

# Document ingestion (multimodal)
api_router.include_router(
    document.router,
    prefix="/memory/document",
    tags=["Memory", "Multimodal"],
)

# Image ingestion (multimodal)
api_router.include_router(
    image.router,
    prefix="/memory/image",
    tags=["Memory", "Multimodal"],
)

# Audio ingestion (multimodal)
api_router.include_router(
    audio.router,
    prefix="/memory/audio",
    tags=["Memory", "Multimodal"],
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
