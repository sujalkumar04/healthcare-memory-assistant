"""Test Qdrant Cloud search."""
from app.db.qdrant_client import qdrant_manager
from app.embedding import embedder

client = qdrant_manager.client

# Embed a query
query_vector = embedder.embed_text("patient psychological symptoms")

# Search WITHOUT filter
results = client.query_points(
    collection_name="patient_memories",
    query=query_vector,
    limit=5,
).points

print(f"Results: {len(results)}")
for r in results:
    patient = r.payload.get("patient_id", "unknown")
    content = r.payload.get("content", "")[:50]
    print(f"Score: {r.score:.3f} | Patient: {patient} | Content: {content}")
