"""Document ingestion endpoint for multimodal memory."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.memory.manager import memory_manager
from app.multimodal.document import document_processor

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class DocumentIngestResponse(BaseModel):
    """Response from document ingestion."""
    action: str = Field(..., description="Action taken: created | reinforced")
    point_ids: list[str] = Field(..., description="Created/reinforced memory IDs")
    chunks_stored: int = Field(..., description="Number of chunks stored")
    patient_id: str
    filename: str
    page_count: int
    modality: str = "document"


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a PDF document",
    description="Upload and ingest a PDF document as patient memory.",
)
async def ingest_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    patient_id: str = Form(..., description="Patient identifier"),
    memory_type: str = Form(default="clinical", description="Memory type"),
):
    """
    Ingest a PDF document as patient memory.

    Pipeline:
    1. Extract text from PDF using PyMuPDF
    2. Preprocess and chunk extracted text
    3. Embed each chunk
    4. Store with modality="document", source="pdf"

    Limitations:
    - Text-based PDFs only (no OCR)
    - Handwritten documents not supported
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported. Upload a .pdf file.",
        )

    # Validate patient_id
    if not patient_id or not patient_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="patient_id is required",
        )

    try:
        # Read file content
        pdf_bytes = await file.read()

        # Extract text from PDF
        extraction = document_processor.extract_text_from_bytes(
            pdf_bytes=pdf_bytes,
            filename=file.filename,
        )

        if not extraction.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"PDF extraction failed: {extraction.error}",
            )

        if not extraction.text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No text could be extracted from PDF. It may be scanned/image-based.",
            )

        # Prepare metadata
        metadata = {
            "original_filename": file.filename,
            "page_count": extraction.page_count,
            "extraction_method": extraction.extraction_method,
            "file_size_bytes": len(pdf_bytes),
        }

        # Ingest using existing memory manager
        result = await memory_manager.ingest_memory(
            patient_id=patient_id.strip(),
            raw_text=extraction.text,
            memory_type=memory_type,
            source="pdf",
            modality="document",
            metadata=metadata,
            check_reinforcement=True,
        )

        return DocumentIngestResponse(
            action=result["action"],
            point_ids=result["point_ids"],
            chunks_stored=len(result["point_ids"]),
            patient_id=patient_id.strip(),
            filename=file.filename,
            page_count=extraction.page_count,
            modality="document",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(e)}",
        )
