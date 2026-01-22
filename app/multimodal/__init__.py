"""
Multimodal processors for document, image, and audio ingestion.

This module provides text extraction and embedding from various file formats
to enable multimodal memory storage in the healthcare assistant.
"""

from app.multimodal.document import DocumentProcessor, document_processor
from app.multimodal.image import ImageProcessor, image_processor
from app.multimodal.audio import AudioProcessor, audio_processor

__all__ = [
    "DocumentProcessor",
    "document_processor",
    "ImageProcessor",
    "image_processor",
    "AudioProcessor",
    "audio_processor",
]
