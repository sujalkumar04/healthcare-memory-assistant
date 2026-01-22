"""
Image Processor (CLIP Vision Embeddings)

Generates image embeddings using CLIP for multimodal memory storage.
Uses the CLIP ViT-B/32 model through the clip-as-service or transformers library.

LIMITATIONS:
- No medical image analysis or diagnosis
- No interpretation of findings
- Images stored as retrievable context only
"""

from dataclasses import dataclass
from typing import BinaryIO
from PIL import Image
import io


@dataclass
class ImageProcessingResult:
    """Result of image processing."""
    embedding: list[float]
    width: int
    height: int
    format: str
    filename: str
    success: bool = True
    error: str | None = None


class ImageProcessor:
    """
    Generates image embeddings using CLIP.
    
    Uses CLIP ViT-B/32 for 512-dimensional image embeddings.
    Images are preprocessed to 224x224 before embedding.
    
    NOT IMPLEMENTED:
    - Medical image analysis
    - Diagnosis or interpretation
    - Anomaly detection
    - Report generation
    """

    def __init__(self):
        self._model = None
        self._processor = None

    def _load_model(self):
        """Lazy-load CLIP model to avoid import errors when not installed."""
        if self._model is None:
            try:
                from transformers import CLIPProcessor, CLIPModel
                
                model_name = "openai/clip-vit-base-patch32"
                self._processor = CLIPProcessor.from_pretrained(model_name)
                self._model = CLIPModel.from_pretrained(model_name)
                self._model.eval()
            except ImportError:
                raise ImportError(
                    "transformers and torch are required for image processing. "
                    "Install with: pip install transformers torch pillow"
                )
        return self._model, self._processor

    def embed_image_from_bytes(
        self,
        image_bytes: bytes,
        filename: str = "image.jpg",
    ) -> ImageProcessingResult:
        """
        Generate embedding from image bytes.

        Args:
            image_bytes: Raw image file bytes
            filename: Original filename for metadata

        Returns:
            ImageProcessingResult with 512-dim embedding
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed (CLIP expects RGB)
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Get image metadata
            width, height = image.size
            img_format = image.format or "UNKNOWN"
            
            # Load model and process
            model, processor = self._load_model()
            
            # Preprocess image for CLIP
            inputs = processor(images=image, return_tensors="pt")
            
            # Generate embedding
            import torch
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                # Normalize embedding
                embedding = image_features / image_features.norm(dim=-1, keepdim=True)
                embedding = embedding.squeeze().tolist()
            
            return ImageProcessingResult(
                embedding=embedding,
                width=width,
                height=height,
                format=img_format,
                filename=filename,
                success=True,
            )
            
        except Exception as e:
            return ImageProcessingResult(
                embedding=[],
                width=0,
                height=0,
                format="",
                filename=filename,
                success=False,
                error=f"Image processing failed: {str(e)}"
            )

    def embed_image_from_file(
        self,
        file: BinaryIO,
        filename: str = "image.jpg",
    ) -> ImageProcessingResult:
        """
        Generate embedding from a file-like object.

        Args:
            file: File-like object with image content
            filename: Original filename

        Returns:
            ImageProcessingResult with embedding
        """
        image_bytes = file.read()
        return self.embed_image_from_bytes(image_bytes, filename)

    @property
    def embedding_dimension(self) -> int:
        """Return the embedding dimension (512 for CLIP ViT-B/32)."""
        return 512


# Singleton instance
image_processor = ImageProcessor()
