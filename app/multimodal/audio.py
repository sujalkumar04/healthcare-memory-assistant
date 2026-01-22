"""
Audio Processor (Groq Whisper Transcription)

Transcribes audio files to text using Groq Whisper API for multimodal memory storage.
Transcribed text is then processed through the standard text embedding pipeline.

SUPPORTED FORMATS:
- MP3, WAV, M4A, WEBM, OGG, FLAC

LIMITATIONS:
- Max duration: 30 minutes (Groq API limit)
- English-primary transcription
- No speaker diarization
- No emotion/tone detection
"""

import os
from dataclasses import dataclass
from typing import BinaryIO

from groq import Groq

from app.core.config import settings


# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".webm", ".ogg", ".flac"}

# Maximum audio duration in seconds (30 minutes)
MAX_AUDIO_DURATION_SECONDS = 1800

# Maximum file size in bytes (25 MB - Groq limit)
MAX_AUDIO_FILE_SIZE = 25 * 1024 * 1024


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""
    transcript: str
    duration_seconds: float | None
    language: str
    filename: str
    success: bool = True
    error: str | None = None


class AudioProcessor:
    """
    Transcribes audio files using Groq Whisper API.
    
    Uses Groq's whisper-large-v3-turbo model for fast, accurate transcription.
    Transcribed text is then handled by the standard text embedding pipeline.
    
    NOT IMPLEMENTED:
    - Speaker diarization
    - Emotion/tone detection
    - Real-time streaming transcription
    - Audio embeddings (using text transcription instead)
    """

    def __init__(self):
        self._client: Groq | None = None

    @property
    def client(self) -> Groq:
        """Lazy-load Groq client."""
        if self._client is None:
            api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not configured for audio transcription")
            self._client = Groq(api_key=api_key)
        return self._client

    def validate_audio_file(
        self,
        filename: str,
        file_size: int,
    ) -> tuple[bool, str | None]:
        """
        Validate audio file before processing.

        Args:
            filename: Original filename
            file_size: File size in bytes

        Returns:
            (is_valid, error_message)
        """
        # Check file extension
        ext = os.path.splitext(filename.lower())[1]
        if ext not in SUPPORTED_AUDIO_FORMATS:
            return False, f"Unsupported audio format: {ext}. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"

        # Check file size
        if file_size > MAX_AUDIO_FILE_SIZE:
            max_mb = MAX_AUDIO_FILE_SIZE / (1024 * 1024)
            return False, f"Audio file too large. Maximum size: {max_mb:.0f} MB"

        return True, None

    async def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.mp3",
        language: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio bytes using Groq Whisper API.

        Args:
            audio_bytes: Raw audio file bytes
            filename: Original filename (for format detection)
            language: Optional language code (e.g., 'en', 'es'). Auto-detected if None.

        Returns:
            TranscriptionResult with transcript text
        """
        # Validate file
        is_valid, error = self.validate_audio_file(filename, len(audio_bytes))
        if not is_valid:
            return TranscriptionResult(
                transcript="",
                duration_seconds=None,
                language="",
                filename=filename,
                success=False,
                error=error,
            )

        try:
            # Create a file-like object for Groq API
            import io
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename  # Groq needs filename for format detection

            # Call Groq Whisper API
            transcription = self.client.audio.transcriptions.create(
                file=(filename, audio_file),
                model="whisper-large-v3-turbo",
                language=language,  # None = auto-detect
                response_format="verbose_json",  # Get duration info
            )

            # Extract transcript and metadata
            transcript_text = transcription.text or ""
            duration = getattr(transcription, "duration", None)
            detected_language = getattr(transcription, "language", language or "en")

            return TranscriptionResult(
                transcript=transcript_text.strip(),
                duration_seconds=duration,
                language=detected_language,
                filename=filename,
                success=True,
            )

        except Exception as e:
            return TranscriptionResult(
                transcript="",
                duration_seconds=None,
                language="",
                filename=filename,
                success=False,
                error=f"Transcription failed: {str(e)}",
            )

    async def transcribe_audio_file(
        self,
        file: BinaryIO,
        filename: str = "audio.mp3",
        language: str | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio from a file-like object.

        Args:
            file: File-like object with audio content
            filename: Original filename
            language: Optional language code

        Returns:
            TranscriptionResult with transcript
        """
        audio_bytes = file.read()
        return await self.transcribe_audio_bytes(audio_bytes, filename, language)


# Singleton instance
audio_processor = AudioProcessor()
