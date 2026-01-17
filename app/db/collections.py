"""Qdrant collection schema definitions."""

from qdrant_client.http import models

# =============================================================================
# COLLECTION: patient_memories
# =============================================================================
# Primary collection for storing healthcare memories with patient isolation.
#
# Vector: 384-dim (sentence-transformers/all-MiniLM-L6-v2)
# Distance: Cosine similarity
# =============================================================================

COLLECTION_NAME = "patient_memories"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension
DISTANCE_METRIC = models.Distance.COSINE

# Payload field definitions for indexing
PAYLOAD_INDEXES = [
    # patient_id: REQUIRED filter for all queries (patient isolation)
    {"field_name": "patient_id", "schema": models.PayloadSchemaType.KEYWORD},
    
    # memory_type: clinical | mental_health | medication | note
    {"field_name": "memory_type", "schema": models.PayloadSchemaType.KEYWORD},
    
    # source: session | doctor | import
    {"field_name": "source", "schema": models.PayloadSchemaType.KEYWORD},
    
    # created_at: for temporal queries
    {"field_name": "created_at", "schema": models.PayloadSchemaType.DATETIME},
]

# Full payload structure (for documentation)
PAYLOAD_SCHEMA = {
    "patient_id": "keyword (required)",      # Patient isolation key
    "memory_type": "keyword",                # clinical | mental_health | medication | note
    "content": "text",                       # Original memory content
    "source": "keyword",                     # session | doctor | import
    "created_at": "datetime",                # ISO format timestamp
    "confidence": "float",                   # 0.0 - 1.0 confidence score
    "metadata": "json",                      # Additional structured data
}


def get_collection_config() -> dict:
    """Get collection configuration for creation."""
    return {
        "collection_name": COLLECTION_NAME,
        "vectors_config": models.VectorParams(
            size=VECTOR_SIZE,
            distance=DISTANCE_METRIC,
        ),
    }


def get_payload_indexes() -> list[dict]:
    """Get payload index definitions."""
    return PAYLOAD_INDEXES
