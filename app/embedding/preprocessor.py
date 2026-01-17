"""
Text preprocessing for healthcare memories.

Normalizes text while preserving medical terminology.
"""

import re
from typing import Callable


class TextPreprocessor:
    """
    Preprocesses text for embedding while preserving medical terms.
    
    Pipeline:
    1. Normalize whitespace
    2. Lowercase (preserves meaning for embeddings)
    3. Clean excessive punctuation
    4. Keep medical terminology intact
    """

    # Common medical abbreviations to preserve
    MEDICAL_ABBREVS = {
        "mg", "ml", "kg", "bp", "hr", "bpm", "mmhg",
        "prn", "bid", "tid", "qid", "qd", "qhs",
        "po", "iv", "im", "sq", "sl",
        "hba1c", "ldl", "hdl", "bmi", "ekg", "ecg",
        "ct", "mri", "cbc", "bmp", "cmp",
    }

    def __init__(self):
        self._pipeline: list[Callable[[str], str]] = [
            self.normalize_whitespace,
            self.lowercase,
            self.clean_punctuation,
        ]

    def process(self, text: str) -> str:
        """Run text through the preprocessing pipeline."""
        if not text:
            return ""
        
        for step in self._pipeline:
            text = step(text)
        
        return text.strip()

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize all whitespace to single spaces.
        Handles tabs, newlines, and multiple spaces.
        """
        # Replace newlines and tabs with spaces
        text = re.sub(r"[\r\n\t]+", " ", text)
        # Collapse multiple spaces
        text = re.sub(r" +", " ", text)
        return text.strip()

    @staticmethod
    def lowercase(text: str) -> str:
        """Convert to lowercase for consistent embeddings."""
        return text.lower()

    @staticmethod
    def clean_punctuation(text: str) -> str:
        """
        Remove excessive punctuation while keeping meaningful ones.
        Preserves: periods, commas, colons, hyphens, slashes (medical notation)
        """
        # Remove repeated punctuation (e.g., "!!!" -> "!")
        text = re.sub(r"([.!?,;:])\1+", r"\1", text)
        
        # Remove standalone special characters but keep medical notation
        # Keep: . , : ; - / ( ) for medical terms like "10mg/day" or "bp: 120/80"
        text = re.sub(r"[#@$%^&*_+=\[\]{}|\\<>~`]+", " ", text)
        
        # Clean up any double spaces created
        text = re.sub(r" +", " ", text)
        
        return text

    def process_for_storage(self, text: str) -> str:
        """
        Light preprocessing for storage (keeps more original form).
        Only normalizes whitespace, doesn't lowercase.
        """
        return self.normalize_whitespace(text)


# Singleton instance
preprocessor = TextPreprocessor()
