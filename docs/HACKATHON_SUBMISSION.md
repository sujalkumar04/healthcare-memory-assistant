# Healthcare Memory Assistant

**Qdrant Convolve 4.0 Hackathon Submission**

---

## 1. Problem Statement

### The Fragmentation Problem

Healthcare providers face a simple but dangerous problem: patient information is scattered across time.

A psychiatrist seeing a patient today might need to recall a stressor mentioned three months ago, or a side effect reported to a different clinician last year. With caseloads often exceeding 30 patients, remembering every individual's narrative arc is humanly impossible.

Clinicians spend the first 10 minutes of appointments just trying to "catch up." They scroll through fragmented EMR notes, hoping to spot the relevant detail. Critical connections get missed. Patients repeat their stories. Providers burn out.

### Why This Matters

Mental health treatment depends on **longitudinal context**. A pattern of sleep disturbance over six months is clinically significant. A single bad night is noise. Without a system to track and surface these patterns, insights get lost in the flood of daily notes.

### The AI Risk

Generative AI promises to help—summarizing records, answering questions, surfacing patterns. But it introduces a fatal flaw for healthcare: **hallucination**.

A standard AI system that guesses or fills gaps isn't just unhelpful—it's dangerous. In clinical settings, "I don't know" is a safe answer. A fabricated fact could be malpractice.

**Our approach:** Build an AI that refuses to answer when it lacks evidence. Silence is safer than confident fabrication.

---

## 2. System Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (HTML/JS)                        │
│        Ingest Panel · Search Panel · Timeline View          │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│      /memory · /search · /patient · /health endpoints       │
└─────────────────────────────────────────────────────────────┘
          │                    │                     │
          ▼                    ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Memory    │       │  Retrieval  │       │  Reasoning  │
│   Manager   │       │   Engine    │       │    Chain    │
└─────────────┘       └─────────────┘       └─────────────┘
          │                    │                     │
          └────────────────────┼─────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Qdrant Vector Database                    │
│    patient_memories (384-dim) · patient_images (512-dim)    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | What It Does |
|-----------|--------------|
| **Memory Manager** | Ingests data, chunks text, detects similar memories, applies reinforcement and decay |
| **Retrieval Engine** | Embeds queries, searches Qdrant with patient filtering, ranks results by combined score |
| **Reasoning Chain** | Constructs prompts from evidence, calls LLM, enforces anti-hallucination gate |
| **Qdrant Operations** | CRUD operations with mandatory patient isolation on every query |

### Why Qdrant is Critical

Qdrant isn't just storage—it's the enforcement engine for our core requirements.

**1. Semantic Search**

Patients describe symptoms differently every time. "I can't shut my brain off" and "racing thoughts" mean the same thing but share no keywords. Vector similarity connects concepts that keyword search would miss.

**2. Patient Isolation via Payload Filtering**

Every database query includes a mandatory `patient_id` filter. This isn't a best practice—it's hard-coded into the retrieval logic. One patient's data can never appear in another patient's results.

**3. Metadata-Rich Lifecycle Management**

Each memory stores:
- `confidence` scores (change over time via reinforcement/decay)
- `modality` tags (text, document, image, audio)
- `is_active` flags (soft deletion for audit trail)

This enables complex filtering and ranking inside the database, keeping application logic clean.

**4. Separate Collections for Modalities**

Text and documents use 384-dimensional MiniLM embeddings. Images use 512-dimensional CLIP embeddings. Separate collections with appropriate vector configurations.

---

## 3. Multimodal Strategy

### Supported Data Types

| Modality | Status | Method | Embedding |
|----------|--------|--------|-----------|
| **Text** | ✅ Implemented | Direct embedding | MiniLM (384-dim) |
| **PDF Documents** | ✅ Implemented | PyMuPDF text extraction → chunking → embedding | MiniLM (384-dim) |
| **Audio** | ✅ Implemented | Groq Whisper transcription → text embedding | MiniLM (384-dim) |
| **Images** | ✅ Implemented | CLIP ViT-B/32 visual encoding | CLIP (512-dim) |

### How It Works

**Text, Documents, and Audio** all end up as text. They share the same 384-dimensional vector space in the `patient_memories` collection. A single query can retrieve typed notes, transcribed session recordings, and PDF referral letters simultaneously.

**Images** live in a separate `patient_images` collection with 512-dimensional CLIP vectors. Image search uses CLIP's text encoder to embed the query, then finds visually similar images.

**Multimodal Search** queries both collections in parallel and merges results into a unified ranked list.

### What is NOT Implemented

- **OCR for scanned PDFs** — Only text-based PDFs work
- **Speaker diarization** — Audio transcription doesn't identify who said what
- **Emotion detection** — No tone or sentiment analysis
- **Medical image analysis** — Images are stored as references only; the system does not interpret X-rays, scans, or any medical imagery
- **Image diagnosis** — Explicitly forbidden in prompts

---

## 4. Search / Memory / Recommendation Logic

### Ingestion Pipeline

1. Raw content arrives via API
2. Text is preprocessed (whitespace normalization, punctuation cleanup)
3. Chunker splits into 200-300 word segments with 30-word overlap
4. Each chunk is embedded to a 384-dim vector
5. System checks for similar existing memories (cosine > 0.85):
   - **If found:** Reinforce existing memory (+0.15 confidence boost)
   - **If not:** Insert new memory with confidence 1.0
6. Store in Qdrant with full metadata payload

### Retrieval Pipeline

1. User query embedded to 384-dim vector
2. Qdrant search with **mandatory** `patient_id` filter
3. Filter out inactive (soft-deleted) memories
4. Calculate combined score: `0.7 × semantic + 0.3 × confidence`
5. Return ranked evidence list

### Memory Reinforcement

When a new memory is ingested that's semantically identical to an existing one, we don't duplicate. We boost the existing memory's confidence by +0.15 (capped at 1.0).

Repetition signals importance. Information mentioned across multiple sessions becomes more prominent in search results.

### Memory Decay

Unused memories fade over time. Confidence decays with a 90-day half-life:

- **Grace period:** No decay for the first 7 days
- **Decay formula:** `confidence × (0.5 ^ (days / 90))`
- **Floor:** Never drops below 0.1

This ensures recent, relevant data surfaces first while preserving an audit trail of older information.

### Anti-Hallucination Safeguards

This is the most important logic in the system.

```python
if not evidence:
    return "Insufficient data in patient records..."
    # LLM is NEVER called
```

**The gate works like this:**

1. Retrieval runs first. We search Qdrant for relevant memories.
2. If the evidence list is empty → return a fixed safe response. The LLM is never invoked.
3. If evidence exists → construct a prompt containing only the retrieved snippets.
4. LLM is explicitly instructed: "Use ONLY the provided evidence. If insufficient, say so."

By physically preventing the LLM from seeing the query when no data exists, we eliminate the possibility of fabrication.

### Evidence-Based Reasoning

When evidence exists, the LLM receives:
- The retrieved memory snippets
- Explicit grounding rules
- Instructions to say "Insufficient data" if evidence is weak

Every response includes:
- A disclaimer requiring healthcare professional review
- Citation of sources used
- Count of evidence pieces considered

---

## 5. Limitations & Ethics

### Known Failure Modes

| Failure | System Response |
|---------|-----------------|
| No relevant memories found | Returns "Insufficient data" (no LLM called) |
| Poor audio quality | Transcription errors propagate into memory |
| Scanned PDF (image-based) | No text extracted; returns error |
| Specialized medical jargon | Embedding model may miss semantic similarity |
| LLM service unavailable | Returns HTTP 500 with clear error |

### Bias Risks

- **Embedding model:** Trained on general web text, not medical terminology. May underperform on rare conditions or non-English terms.
- **Semantic similarity ≠ clinical relevance:** Two phrases might be semantically similar but clinically different.

### Privacy Considerations

- Patient isolation enforced at application layer
- All demo data is synthetic (no real PHI used)
- **NOT implemented:** End-to-end encryption, audit logging, HIPAA/GDPR compliance

### Safety Boundaries

The system is designed as a **decision support tool**, not an autonomous agent.

**What it does:**
- Organizes and retrieves patient notes
- Summarizes historical information
- Surfaces patterns across sessions

**What it explicitly does NOT do:**
- Provide medical diagnoses
- Recommend treatments
- Replace clinical judgment
- Operate without human oversight
- Handle emergencies
- Interpret medical images

Every output requires verification by a qualified healthcare professional.

### Explicit Non-Goals

- User authentication (out of scope for hackathon)
- Multi-tenant organization support
- Real-time streaming
- Fine-tuned medical embeddings
- Regulatory compliance

---

## 6. Demo / Usage Examples

### Ingest a Memory

```bash
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_001",
    "raw_text": "Patient reports anxiety and trouble sleeping for the past week.",
    "memory_type": "mental_health",
    "source": "session"
  }'
```

### Search Memories

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_001",
    "query": "sleep problems"
  }'
```

### Get a Grounded Answer

```bash
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_001",
    "query": "What symptoms has the patient reported?"
  }'
```

### Prove Anti-Hallucination

```bash
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_001",
    "query": "What is the patient blood pressure?"
  }'
# Returns: "Insufficient data in patient records..."
# The LLM was never called.
```

---

## 7. Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Vector Database | Qdrant 1.16 |
| Text Embeddings | FastEmbed (all-MiniLM-L6-v2, 384-dim) |
| Image Embeddings | CLIP ViT-B/32 (512-dim) |
| PDF Extraction | PyMuPDF |
| Audio Transcription | Groq Whisper API |
| LLM | Groq API (Llama 3.3 70B) |
| Frontend | Static HTML/CSS/JS |
| Deployment | Docker, Docker Compose, Render.com |

---

## 8. Conclusion

We built a memory-first AI system that refuses to guess. When evidence exists, it summarizes. When evidence is missing, it stays silent. This makes it safer for healthcare contexts where fabrication is unacceptable.

Qdrant powers the core: semantic search, patient isolation, and metadata-driven lifecycle management. The LLM is just the translator—Qdrant is the brain.

---

*Prepared for Qdrant Convolve 4.0 Hackathon*

*All demo data is synthetic. This system is not validated for clinical use.*
