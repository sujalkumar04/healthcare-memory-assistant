"""Embedding module initialization."""

from app.embedding.embedder import embedder
from app.embedding.chunker import chunker
from app.embedding.preprocessor import preprocessor

__all__ = ["embedder", "chunker", "preprocessor"]
