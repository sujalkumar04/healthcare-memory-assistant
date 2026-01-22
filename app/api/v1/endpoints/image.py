"""Image ingestion endpoint for multimodal memory."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.db.image_operations import image_ops
from app.multimodal.image import image_processor

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class ImageIngestResponse(BaseModel):
    """Response from image ingestion."""
    point_id: str = Field(..., description="Stored image ID")
    patient_id: str
    filename: str
    width: int
    height: int
    format: str
    modality: str = "image"
    message: str = "Image stored successfully"


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "",
    response_model=ImageIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest an image",
    description="Upload and store an image as patient memory using CLIP embeddings.",
)
async def ingest_image(
    file: UploadFile = File(..., description="Image file (PNG, JPEG)"),
    patient_id: str = Form(..., description="Patient identifier"),
    memory_type: str = Form(default="clinical", description="Image type"),
    description: str = Form(default="", description="Optional image description"),
):
    """
    Ingest an image as patient memory.

    Pipeline:
    1. Validate image format (PNG, JPEG)
    2. Generate CLIP embedding (512-dim)
    3. Store in patient_images collection with patient isolation

    IMPORTANT RESTRICTIONS:
    - Images are stored as retrievable context ONLY
    - NO medical analysis or diagnosis
    - NO interpretation of findings
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    
    valid_extensions = (".png", ".jpg", ".jpeg")
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only image files are supported: {valid_extensions}",
        )

    # Validate patient_id
    if not patient_id or not patient_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id is required",
        )

    try:
        # Read image bytes
        image_bytes = await file.read()

        # Generate CLIP embedding
        result = image_processor.embed_image_from_bytes(
            image_bytes=image_bytes,
            filename=file.filename,
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Image processing failed: {result.error}",
            )

        # Prepare metadata
        metadata = {
            "original_filename": file.filename,
            "width": result.width,
            "height": result.height,
            "format": result.format,
            "file_size_bytes": len(image_bytes),
            "embedding_model": "clip-vit-base-patch32",
            "is_active": True,
        }

        # Store in Qdrant image collection
        point_id = await image_ops.upsert_image(
            vector=result.embedding,
            patient_id=patient_id.strip(),
            description=description,
            memory_type=memory_type,
            source="upload",
            confidence=1.0,
            metadata=metadata,
        )

        return ImageIngestResponse(
            point_id=point_id,
            patient_id=patient_id.strip(),
            filename=file.filename,
            width=result.width,
            height=result.height,
            format=result.format,
            modality="image",
            message="Image stored successfully. Note: Images are retrievable context only - no medical analysis performed.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image ingestion failed: {str(e)}",
        )
