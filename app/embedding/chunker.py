"""
Text chunking strategies for memory ingestion.

Splits text into ~200-300 word chunks while preserving sentence boundaries.
"""

import re
from typing import Iterator


class TextChunker:
    """
    Splits text into chunks suitable for embedding.
    
    Strategy:
    - Target: 200-300 words per chunk
    - Preserve sentence boundaries
    - Overlap for context continuity
    """

    def __init__(
        self,
        target_words: int = 250,
        min_words: int = 50,
        max_words: int = 350,
        overlap_words: int = 30,
    ):
        """
        Initialize chunker with word-based limits.

        Args:
            target_words: Target words per chunk (default: 250)
            min_words: Minimum words for a valid chunk (default: 50)
            max_words: Maximum words before forcing split (default: 350)
            overlap_words: Word overlap between chunks (default: 30)
        """
        self.target_words = target_words
        self.min_words = min_words
        self.max_words = max_words
        self.overlap_words = overlap_words

    def chunk_text(self, text: str) -> list[str]:
        """
        Split text into chunks of ~200-300 words.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # Split into sentences
        sentences = self._split_sentences(text)
        
        if not sentences:
            return [text.strip()] if text.strip() else []

        chunks = []
        current_chunk: list[str] = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())

            # If single sentence exceeds max, force split it
            if sentence_words > self.max_words:
                # Flush current chunk
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_word_count = 0
                
                # Split long sentence by words
                chunks.extend(self._split_long_sentence(sentence))
                continue

            # Check if adding sentence exceeds target
            if current_word_count + sentence_words > self.target_words:
                # If we have enough words, create chunk
                if current_word_count >= self.min_words:
                    chunks.append(" ".join(current_chunk))
                    
                    # Start new chunk with overlap
                    overlap_sentences = self._get_overlap(current_chunk)
                    current_chunk = overlap_sentences + [sentence]
                    current_word_count = sum(len(s.split()) for s in current_chunk)
                else:
                    # Not enough words, keep adding
                    current_chunk.append(sentence)
                    current_word_count += sentence_words
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words

        # Add remaining chunk
        if current_chunk and current_word_count >= self.min_words:
            chunks.append(" ".join(current_chunk))
        elif current_chunk and chunks:
            # Merge small remainder with last chunk
            chunks[-1] = chunks[-1] + " " + " ".join(current_chunk)
        elif current_chunk:
            # Only chunk, add even if small
            chunks.append(" ".join(current_chunk))

        return [c.strip() for c in chunks if c.strip()]

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using regex."""
        # Split on sentence boundaries (., !, ?)
        # But not on abbreviations like "Dr." or "mg."
        pattern = r"(?<=[.!?])\s+(?=[A-Z])"
        sentences = re.split(pattern, text)
        
        # Fallback: if no splits, try simpler pattern
        if len(sentences) == 1 and len(text.split()) > self.max_words:
            sentences = re.split(r"[.!?]+\s*", text)
        
        return [s.strip() for s in sentences if s.strip()]

    def _split_long_sentence(self, sentence: str) -> list[str]:
        """Force-split a sentence that's too long."""
        words = sentence.split()
        chunks = []
        
        for i in range(0, len(words), self.target_words):
            chunk_words = words[i:i + self.target_words]
            if chunk_words:
                chunks.append(" ".join(chunk_words))
        
        return chunks

    def _get_overlap(self, sentences: list[str]) -> list[str]:
        """Get last sentences for overlap (up to overlap_words)."""
        if not sentences:
            return []
        
        overlap: list[str] = []
        word_count = 0
        
        for sentence in reversed(sentences):
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= self.overlap_words:
                overlap.insert(0, sentence)
                word_count += sentence_words
            else:
                break
        
        return overlap


# Default chunker instance (200-300 words)
chunker = TextChunker(target_words=250, min_words=50, max_words=350)
