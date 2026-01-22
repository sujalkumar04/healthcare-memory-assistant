"""FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from qdrant_client.http import models

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.qdrant_client import qdrant_manager
from app.db.collections import COLLECTION_NAME, VECTOR_SIZE, DISTANCE_METRIC


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await qdrant_manager.connect()
    
    # Ensure collection exists (especially for in-memory mode)
    if not qdrant_manager.collection_exists(COLLECTION_NAME):
        print(f"📦 Creating collection: {COLLECTION_NAME}")
        qdrant_manager.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=DISTANCE_METRIC,
            ),
        )
    
    yield
    # Shutdown
    await qdrant_manager.disconnect()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Healthcare Memory Assistant",
        description="Multi-patient Healthcare & Mental Health Memory Assistant API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    # Mount frontend static files
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

    return app


app = create_app()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Healthcare Memory Assistant",
        "version": "0.1.0",
        "docs": "/docs",
    }
