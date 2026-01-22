"""
Document Processor (PDF Text Extraction)

Extracts text from PDF documents for multimodal memory ingestion.
Uses PyMuPDF (fitz) for efficient text extraction.

LIMITATIONS:
- Text-based PDFs only (no OCR)
- Handwritten documents not supported
- No interpretation or analysis
"""

from dataclasses import dataclass
from typing import BinaryIO
import io


@dataclass
class DocumentExtractionResult:
    """Result of document text extraction."""
    text: str
    page_count: int
    filename: str
    extraction_method: str = "pymupdf"
    success: bool = True
    error: str | None = None


class DocumentProcessor:
    """
    Extracts text from PDF documents.
    
    Uses PyMuPDF for text extraction. Falls back to basic
    extraction if advanced features fail.
    
    NOT IMPLEMENTED:
    - OCR for scanned documents
    - Handwritten text recognition
    - Table/chart extraction
    - Document interpretation
    """

    def __init__(self):
        self._fitz = None

    def _get_fitz(self):
        """Lazy-load PyMuPDF to avoid import errors when not installed."""
        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                raise ImportError(
                    "PyMuPDF (fitz) is required for PDF processing. "
                    "Install with: pip install pymupdf"
                )
        return self._fitz

    def extract_text_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "document.pdf",
    ) -> DocumentExtractionResult:
        """
        Extract text from PDF bytes.

        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Original filename for metadata

        Returns:
            DocumentExtractionResult with extracted text
        """
        try:
            fitz = self._get_fitz()
            
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{page_text.strip()}")
            
            doc.close()
            
            full_text = "\n\n".join(text_parts)
            
            if not full_text.strip():
                return DocumentExtractionResult(
                    text="",
                    page_count=len(doc) if doc else 0,
                    filename=filename,
                    success=False,
                    error="No extractable text found. Document may be scanned/image-based."
                )
            
            return DocumentExtractionResult(
                text=full_text,
                page_count=len(text_parts),
                filename=filename,
                success=True,
            )
            
        except Exception as e:
            return DocumentExtractionResult(
                text="",
                page_count=0,
                filename=filename,
                success=False,
                error=f"PDF extraction failed: {str(e)}"
            )

    def extract_text_from_file(
        self,
        file: BinaryIO,
        filename: str = "document.pdf",
    ) -> DocumentExtractionResult:
        """
        Extract text from a file-like object.

        Args:
            file: File-like object with PDF content
            filename: Original filename

        Returns:
            DocumentExtractionResult with extracted text
        """
        pdf_bytes = file.read()
        return self.extract_text_from_bytes(pdf_bytes, filename)


# Singleton instance
document_processor = DocumentProcessor()
