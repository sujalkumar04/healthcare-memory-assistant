"""Audio ingestion endpoint."""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form

from app.memory.manager import memory_manager

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest audio memory",
    description="Upload audio file for transcription and memory storage.",
)
async def ingest_audio_memory(
    patient_id: str = Form(..., description="Patient identifier"),
    memory_type: str = Form("session", description="Memory type: session | clinical | mental_health"),
    source: str = Form("recording", description="Source: recording | voicemail"),
    file: UploadFile = File(..., description="Audio file (MP3, WAV, M4A, WEBM, OGG, FLAC)"),
):
    """
    Ingest audio memory via transcription.

    Pipeline:
    1. Upload audio file
    2. Transcribe using Groq Whisper API
    3. Chunk and embed transcribed text
    4. Store with modality: "audio"

    Supported formats: MP3, WAV, M4A, WEBM, OGG, FLAC
    Max file size: 25 MB
    Max duration: 30 minutes
    """
    try:
        # Read file content
        audio_bytes = await file.read()
        filename = file.filename or "audio.mp3"

        # Ingest via memory manager
        result = await memory_manager.ingest_audio(
            patient_id=patient_id,
            audio_bytes=audio_bytes,
            filename=filename,
            memory_type=memory_type,
            source=source,
        )

        return {
            "action": result["action"],
            "point_ids": result["point_ids"],
            "chunks_stored": len(result["point_ids"]),
            "patient_id": patient_id,
            "transcript_preview": result.get("transcript", ""),
            "duration_seconds": result.get("duration_seconds"),
            "modality": "audio",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio ingestion failed: {str(e)}",
        )
