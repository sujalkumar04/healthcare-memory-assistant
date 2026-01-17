"""
Embedding engine using fastembed (ONNX-based).

Model: sentence-transformers/all-MiniLM-L6-v2 (via fastembed)
Vector size: 384 dimensions
"""

from fastembed import TextEmbedding

from app.core.config import settings
from app.core.exceptions import EmbeddingError


class Embedder:
    """
    Generates 384-dimensional embeddings using FastEmbed (ONNX).
    
    Model: all-MiniLM-L6-v2
    - Extremely fast inference (ONNX Runtime)
    - Low memory footprint (<200MB vs >1GB for PyTorch)
    - No API key required (runs locally)
    """

    _instance: "Embedder | None" = None
    _model: TextEmbedding | None = None

    def __new__(cls) -> "Embedder":
        """Singleton pattern for model reuse."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> TextEmbedding:
        """Lazy-load the fastembed model."""
        if Embedder._model is None:
            try:
                # FastEmbed downloads and caches the model automatically
                Embedder._model = TextEmbedding(
                    model_name=settings.EMBEDDING_MODEL,
                    fast_model_loading=True
                )
            except Exception as e:
                raise EmbeddingError(f"Failed to load embedding model: {e}")
        return Embedder._model

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            384-dimensional embedding vector
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        try:
            # fastembed returns a generator of vectors
            embedding_gen = self.model.embed([text])
            return list(next(embedding_gen))
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (more efficient).

        Args:
            texts: List of texts to embed

        Returns:
            List of 384-dimensional embedding vectors
        """
        if not texts:
            return []

        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise EmbeddingError("All texts are empty")

        try:
            # list(generator) to get all vectors
            return list(self.model.embed(valid_texts))
        except Exception as e:
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}")

    @property
    def dimension(self) -> int:
        """Return the embedding dimension (384 for all-MiniLM-L6-v2)."""
        return 384


# Singleton instance
embedder = Embedder()
