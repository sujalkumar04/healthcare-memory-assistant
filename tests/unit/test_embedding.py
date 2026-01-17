"""Unit tests for embedding module."""

import pytest
from app.embedding.chunker import TextChunker
from app.embedding.preprocessor import TextPreprocessor


class TestTextChunker:
    """Tests for TextChunker."""

    def test_short_text_single_chunk(self):
        """Test that short text returns single chunk."""
        chunker = TextChunker(chunk_size=100)
        chunks = chunker.chunk_text("Short text")
        assert len(chunks) == 1
        assert chunks[0] == "Short text"

    def test_long_text_multiple_chunks(self):
        """Test that long text is split into chunks."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        long_text = "This is a longer text that should be split into multiple chunks for processing."
        chunks = chunker.chunk_text(long_text)
        assert len(chunks) > 1


class TestTextPreprocessor:
    """Tests for TextPreprocessor."""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        result = TextPreprocessor.normalize_whitespace("  hello   world  ")
        assert result == "hello world"

    def test_redact_ssn(self):
        """Test SSN redaction."""
        result = TextPreprocessor.redact_phi("SSN: 123-45-6789")
        assert "[SSN]" in result
        assert "123-45-6789" not in result

    def test_redact_email(self):
        """Test email redaction."""
        result = TextPreprocessor.redact_phi("Email: test@example.com")
        assert "[EMAIL]" in result
        assert "test@example.com" not in result
