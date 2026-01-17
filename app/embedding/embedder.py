"""
Embedding engine using sentence-transformers.

Model: all-MiniLM-L6-v2
Vector size: 384 dimensions
"""

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.exceptions import EmbeddingError


class Embedder:
    """
    Generates 384-dimensional embeddings using sentence-transformers.
    
    Model: all-MiniLM-L6-v2
    - Fast inference
    - Good quality for semantic similarity
    - No API key required (runs locally)
    """

    _instance: "Embedder | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "Embedder":
        """Singleton pattern for model reuse."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformers model."""
        if Embedder._model is None:
            try:
                Embedder._model = SentenceTransformer(settings.EMBEDDING_MODEL)
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
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalize for cosine similarity
            )
            return embedding.tolist()
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
            embeddings = self.model.encode(
                valid_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}")

    @property
    def dimension(self) -> int:
        """Return the embedding dimension (384 for all-MiniLM-L6-v2)."""
        return 384


# Singleton instance
embedder = Embedder()
