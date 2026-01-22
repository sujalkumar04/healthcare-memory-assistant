# Healthcare Memory Assistant

A memory-first AI system for healthcare decision support with zero-hallucination design.

---

## Problem Statement

Healthcare providers face a fundamental information problem: patient data is fragmented across time and systems. Mental health professionals accumulate session notes, medication histories, and clinical assessments across months or years of treatment. When a patient returns after weeks, clinicians must manually reconstruct context from scattered records.

This fragmentation leads to:
- Incomplete clinical pictures and missed connections between symptoms and treatments
- Cognitive overload for providers managing large patient panels
- Continuity gaps during provider transitions or handoffs
- Lost critical details mentioned in past sessions

Traditional EMRs store data but do not surface it intelligently. Keyword search fails when clinicians cannot predict exact terminology. Generative AI offers a solution but introduces hallucination risk—confidently generating information that never existed.

**Our approach**: An AI system that refuses to answer when it lacks evidence. Silence is safer than confident fabrication.

---

## Key Features

- **Long-term Memory**: Patient data stored as semantic embeddings in Qdrant
- **Evidence-based Reasoning**: LLM answers grounded exclusively in retrieved memories
- **Anti-hallucination Gate**: No evidence = no LLM call; returns fixed safe response
- **Evolving Memory**: Confidence reinforcement for repeated information; time-based decay for stale data
- **Patient Isolation**: All queries scoped to `patient_id` via mandatory Qdrant filtering
- **Multimodal Ingestion**: Text, PDF documents, images, and audio transcription

---

## System Architecture

```
Frontend (HTML/JS)
       |
       v
FastAPI Backend
       |
       +---> Memory Manager (ingestion, chunking, reinforcement, decay)
       +---> Retrieval Engine (semantic search, combined scoring)
       +---> Reasoning Chain (LLM prompting, anti-hallucination gate)
       |
       v
Qdrant Vector Database
  - patient_memories (384-dim, text/docs/audio)
  - patient_images (512-dim, CLIP embeddings)
```

**Component Responsibilities:**

| Component | Function |
|-----------|----------|
| Memory Manager | Ingestion, preprocessing, chunking, reinforcement, decay |
| Retrieval Engine | Semantic search with combined scoring (0.7 semantic + 0.3 confidence) |
| Reasoning Chain | LLM prompting with evidence grounding and anti-hallucination gate |
| Qdrant Operations | CRUD operations with mandatory patient_id filtering |

---

## Why Qdrant

Qdrant is the semantic memory core that enables the entire system:

1. **Semantic Retrieval**: Patient queries rarely match exact keywords. "How is the patient sleeping?" must retrieve notes mentioning "insomnia" or "waking at 3am". Vector similarity handles this naturally.

2. **Payload Filtering**: Every query includes mandatory `patient_id` filter enforced at application layer. Cross-patient data leakage is architecturally impossible.

3. **Metadata-Rich Storage**: Each memory stores confidence scores, memory type, modality, timestamps, and soft-delete flags for lifecycle management.

4. **Separate Collections**: Text/documents use 384-dim MiniLM embeddings; images use 512-dim CLIP embeddings in separate collections.

5. **Production Persistence**: Docker volumes for local development, Qdrant Cloud for production deployment.

---

## Multimodal Strategy

| Modality | Status | Embedding Model | Dimensions |
|----------|--------|-----------------|------------|
| Text | Implemented | all-MiniLM-L6-v2 (FastEmbed) | 384 |
| PDF Documents | Implemented | PyMuPDF extraction + MiniLM | 384 |
| Images | Implemented | CLIP ViT-B/32 | 512 |
| Audio | Implemented | Groq Whisper transcription + MiniLM | 384 |

**Limitations:**
- PDF extraction is text-only (no OCR for scanned documents)
- Images are stored as contextual references only; no image analysis or diagnosis
- Audio is transcribed to text; no speaker diarization or emotion detection

---

## How It Works

### Ingestion Pipeline
1. Raw content received via API
2. Preprocessor normalizes whitespace and punctuation
3. Chunker splits into 200-300 word segments with 30-word overlap
4. Embedder generates 384-dim vector per chunk
5. System checks for similar memories (cosine > 0.85):
   - If found: reinforce existing memory (+0.15 confidence boost)
   - If not: insert new memory with confidence 1.0
6. Store in Qdrant with full metadata payload

### Search Pipeline
1. Query embedded to 384-dim vector
2. Qdrant search with mandatory `patient_id` filter
3. Filter inactive memories, apply min_score threshold (0.2)
4. Calculate combined score: `0.7 * semantic + 0.3 * confidence`
5. Return ranked evidence list

### Reasoning Pipeline
1. Retrieve evidence from Qdrant
2. **Anti-hallucination gate**: If evidence list is empty, return fixed "Insufficient data" response without calling LLM
3. If evidence exists, construct prompt with grounding rules
4. LLM generates answer using only provided evidence
5. Response includes disclaimer and evidence citations

---

## Safety and Anti-Hallucination Design

The primary safety mechanism:

```python
if not evidence:
    return ReasoningResponse(
        answer_text="Insufficient data in patient records...",
        has_context=False,
        evidence_count=0
    )
# LLM is NEVER called when evidence is empty
```

When evidence exists, the LLM is prompted with explicit grounding rules:
- Use ONLY the provided evidence
- Do NOT introduce facts not present in evidence
- If insufficient evidence, state "Insufficient data"
- Do NOT interpret or diagnose from images

All outputs include a disclaimer requiring healthcare professional review.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI 0.128 |
| Vector Database | Qdrant 1.16 |
| Text Embeddings | FastEmbed (all-MiniLM-L6-v2) |
| Image Embeddings | CLIP ViT-B/32 (Transformers) |
| PDF Extraction | PyMuPDF |
| Audio Transcription | Groq Whisper API |
| LLM | Groq API (Llama 3.3 70B) |
| Frontend | Static HTML/CSS/JS |
| Deployment | Docker, Docker Compose, Render.com |

---

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Groq API key
- (Optional) Qdrant Cloud account for production

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd Quadrant

# Configure environment
cp .env.example .env
# Edit .env: add GROQ_API_KEY

# Start services
docker-compose up --build

# Initialize Qdrant collections
docker exec healthcare-backend python scripts/init_collections.py
```

### Access Points
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health
- Qdrant Dashboard: http://localhost:6333/dashboard

---

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/memory` | POST | Ingest text memory |
| `/api/v1/memory/document` | POST | Ingest PDF document |
| `/api/v1/memory/image` | POST | Ingest image |
| `/api/v1/memory/audio` | POST | Ingest audio (transcribe and store) |
| `/api/v1/search` | POST | Semantic search (no LLM) |
| `/api/v1/search/context` | POST | Search with LLM-grounded answer |
| `/api/v1/patient/{id}/summary` | GET | Generate patient summary |
| `/api/v1/patient/{id}/stats` | GET | Memory statistics |
| `/api/v1/health` | GET | Health check |

---

## Limitations and Ethical Considerations

### Technical Constraints
- No user authentication or authorization implemented
- No rate limiting
- No OCR for scanned PDFs
- No hybrid search (vector only, no BM25 fallback)
- Decay scheduling requires manual trigger (no automated cron)
- Embedding model trained on general web text, not medical terminology

### Privacy Considerations
- Patient isolation enforced at application layer
- No end-to-end encryption
- No audit logging
- Not HIPAA/GDPR compliant
- Demo uses synthetic data only

### What This System Does NOT Do
- Provide medical diagnosis or treatment recommendations
- Replace clinical judgment of healthcare professionals
- Operate autonomously without human oversight
- Handle emergency medical situations
- Interpret or diagnose from medical images

---

## Demo Queries

### Ingest a memory
```bash
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","raw_text":"Patient reports anxiety and trouble sleeping.","memory_type":"mental_health","source":"session"}'
```

### Search memories
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","query":"anxiety symptoms"}'
```

### Get grounded answer
```bash
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","query":"What symptoms were reported?"}'
```

### Prove anti-hallucination
```bash
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","query":"What is the blood pressure?"}'
# Returns "Insufficient data" - no hallucination
```

---

## Hackathon Note

This is a prototype developed for Qdrant Convolve 4.0 Hackathon. It is not validated for clinical use and has not undergone regulatory review. All demo data is synthetic. Always consult qualified healthcare professionals for medical decisions.

---

## License

MIT
