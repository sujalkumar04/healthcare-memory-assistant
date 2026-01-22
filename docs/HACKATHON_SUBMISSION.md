# Healthcare Memory Assistant

**Qdrant Convolve 4.0 Hackathon Submission**

---

## 1. Problem Statement

### 1.1 The Societal Issue

Healthcare providers face a fundamental information problem: **patient data is fragmented across time and systems**. Mental health professionals, in particular, accumulate session notes, medication histories, symptom reports, and clinical assessments across months or years of treatment. When a patient returns after weeks, clinicians must manually reconstruct context from scattered records.

This fragmentation creates real harm:

- **Incomplete clinical picture** leads to missed connections between symptoms, treatments, and outcomes
- **Cognitive overload** for providers managing panels of 30+ patients
- **Continuity gaps** when patients transfer between providers or facilities
- **Critical details lost** in handoffs between shifts or specialties

### 1.2 Why This Matters

Mental health treatment depends on longitudinal context more than almost any other specialty. A patient's response to a medication three months ago, a breakthrough in therapy six weeks ago, or a stressor mentioned in passing—these details shape clinical decisions today.

Traditional Electronic Medical Records (EMRs) store data but do not surface it intelligently. Keyword search fails when clinicians cannot predict the exact terminology used in past notes. The result: clinicians spend valuable session time reviewing old records instead of engaging with patients.

### 1.3 The Risk of AI in Healthcare

Generative AI offers a tempting solution—but introduces a dangerous failure mode: **hallucination**. LLMs confidently generate plausible-sounding information that never existed. In healthcare, a hallucinated medication history or fabricated symptom could directly harm patients.

> **Our core philosophy**: An AI system in healthcare should refuse to answer when it lacks evidence, rather than guess. Silence is safer than confident fabrication.

### 1.4 Target Users

- **Mental health professionals**: Psychiatrists, psychologists, licensed counselors
- **Clinical support staff**: Recording and retrieving patient observations
- **Healthcare administrators**: Ensuring continuity of care across providers

---

## 2. System Design

### 2.1 Architecture Overview

The Healthcare Memory Assistant is a three-tier application built around a memory-first architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (HTML/JS)                        │
│              Ingest Panel · Search Panel · Timeline         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                            │
│     /memory · /search · /patient · /health endpoints        │
└─────────────────────────────────────────────────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Memory    │       │  Retrieval  │       │  Reasoning  │
│   Manager   │       │   Engine    │       │    Chain    │
└─────────────┘       └─────────────┘       └─────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Qdrant                              │
│   patient_memories (384-dim) · patient_images (512-dim)     │
│              Cosine Similarity · Payload Filtering          │
└─────────────────────────────────────────────────────────────┘
```

**Component Responsibilities:**

| Component | Responsibility |
|-----------|----------------|
| **Memory Manager** | Ingestion, chunking, reinforcement, decay |
| **Retrieval Engine** | Semantic search with combined scoring |
| **Reasoning Chain** | LLM prompting with anti-hallucination gate |
| **Qdrant Operations** | CRUD with mandatory patient isolation |

### 2.2 Why Qdrant is Critical

Qdrant is not an optional component—it is the semantic memory core that enables the entire system. Without Qdrant, this architecture would not function.

**1. Semantic Retrieval Solves the Vocabulary Problem**

Patient queries rarely match exact keywords. When a clinician asks "How is the patient sleeping?", the system must retrieve notes mentioning "insomnia", "waking at 3am", or "restless nights"—none of which contain the word "sleeping". Vector similarity search handles this naturally; keyword search cannot.

**2. Payload Filtering Enables Patient Isolation**

Every Qdrant query includes a mandatory `patient_id` filter. This is enforced at the application layer:

```python
must_conditions = [
    models.FieldCondition(
        key="patient_id",
        match=models.MatchValue(value=patient_id),
    )
]
```

Qdrant's native payload filtering ensures this happens at query time with no performance penalty. Cross-patient data leakage is architecturally impossible.

**3. Metadata-Rich Storage Enables Evolving Memory**

Each memory point stores not just the vector, but rich payload:
- `confidence` score (for decay/reinforcement)
- `memory_type` (clinical, mental_health, medication)
- `modality` (text, document, image)
- `created_at`, `updated_at` timestamps
- `is_active` flag for soft delete

This enables filtering, ranking, and lifecycle management beyond raw similarity.

**4. Separate Collections for Different Embedding Spaces**

Text/documents use 384-dimensional MiniLM embeddings. Images use 512-dimensional CLIP embeddings. Qdrant's collection architecture keeps these separate while allowing unified API design.

**5. Production-Ready Persistence**

Docker volumes for local development, Qdrant Cloud for production. No code changes required—only environment variables.

### 2.3 Data Flow

**Ingestion Pipeline:**
1. Raw text received via `POST /api/v1/memory`
2. Preprocessor normalizes whitespace, cleans punctuation
3. Chunker splits into 200-300 word segments with 30-word overlap
4. Embedder generates 384-dim vector per chunk
5. System checks for similar memories (cosine > 0.85):
   - If found → reinforce existing memory (+0.15 confidence boost)
   - If not → insert new memory with `confidence: 1.0`
6. Store in Qdrant with full payload

**Search Pipeline:**
1. Query received via `POST /api/v1/search`
2. Query embedded to 384-dim vector
3. Qdrant search with mandatory `patient_id` filter
4. Filter inactive memories, apply `min_score` threshold (0.2)
5. Calculate combined score: `0.7 × semantic + 0.3 × confidence`
6. Return ranked evidence list

**Reasoning Pipeline:**
1. `POST /api/v1/search/context` triggers retrieval + reasoning
2. **ANTI-HALLUCINATION GATE**: If evidence list is empty → return fixed "Insufficient data" response (NO LLM call)
3. If evidence exists → construct prompt with grounding rules
4. LLM generates answer using ONLY provided evidence
5. Response includes disclaimer and evidence citations

---

## 3. Multimodal Strategy

### 3.1 Supported Modalities

| Modality | Status | Embedding Model | Dimensions | Collection |
|----------|--------|-----------------|------------|------------|
| **Text** | ✅ Implemented | all-MiniLM-L6-v2 (FastEmbed) | 384 | `patient_memories` |
| **PDF Documents** | ✅ Implemented | PyMuPDF text extraction → MiniLM | 384 | `patient_memories` |
| **Images** | ✅ Implemented | CLIP ViT-B/32 | 512 | `patient_images` |
| **Audio** | ✅ Implemented | Groq Whisper → text → MiniLM | 384 | `patient_memories` |

### 3.2 Embedding Creation

**Text Memories:**
```python
# Preprocessing
processed_text = preprocessor.process(raw_text)  # Normalize whitespace, clean punctuation

# Chunking
chunks = chunker.chunk_text(processed_text)  # 200-300 words, 30-word overlap

# Embedding
for chunk in chunks:
    vector = embedder.embed_text(chunk)  # 384-dim via FastEmbed
```

**PDF Documents:**
```python
# Extraction (text-based PDFs only)
text = fitz.open(pdf_path).get_page_text(page_num)

# Same chunking and embedding as text
# Stored with modality: "document", source: "pdf"
```

**Audio (Voice Memos/Session Recordings):**
```python
# Transcription via Groq Whisper API
result = await audio_processor.transcribe_audio_bytes(audio_bytes, filename)

# Transcribed text → standard text pipeline
# Stored with modality: "audio", source: "recording"
# Metadata includes: duration_seconds, detected_language
```

**Images:**
```python
# CLIP preprocessing
image = Image.open(image_bytes).convert("RGB")
inputs = processor(images=image, return_tensors="pt")

# CLIP embedding
image_features = model.get_image_features(**inputs)
vector = image_features.squeeze().tolist()  # 512-dim
```

### 3.3 Qdrant Collection Configuration

**Collection: `patient_memories`**
```json
{
  "vectors": { "size": 384, "distance": "Cosine" },
  "payload_schema": {
    "patient_id": "keyword",
    "content": "text",
    "memory_type": "keyword",
    "modality": "keyword",
    "source": "keyword",
    "confidence": "float",
    "created_at": "datetime"
  }
}
```

**Collection: `patient_images`**
```json
{
  "vectors": { "size": 512, "distance": "Cosine" },
  "payload_schema": {
    "patient_id": "keyword",
    "description": "text",
    "memory_type": "keyword",
    "modality": "keyword",
    "metadata": { "original_filename": "keyword", "width": "integer", "height": "integer" }
  }
}
```

### 3.4 Multimodal Querying

Text queries can retrieve across modalities:

```python
# Text/document retrieval (384-dim query)
text_evidence = await retrieval_engine.retrieve(
    patient_id=patient_id,
    query=query,
    modalities=["text", "document"]
)

# Image retrieval (query encoded via CLIP text encoder → 512-dim)
image_evidence = await retrieval_engine.retrieve_images(
    patient_id=patient_id,
    query=query
)

# Combined multimodal retrieval
all_evidence = await retrieval_engine.retrieve_multimodal(
    patient_id=patient_id,
    query=query,
    modalities=["text", "document", "image"]
)
```

### 3.5 Critical Image Restriction

Images are stored and retrieved as **contextual references only**. The system explicitly forbids image interpretation or diagnosis.

When images appear in LLM prompts, they include this warning:
```
[IMAGE: chest_xray.jpg]
[NOTE: Image reference only - do NOT interpret or diagnose from this image]
```

The LLM system prompt reinforces:
> "Do NOT interpret, analyze, or diagnose based on images. Images are contextual references ONLY, not diagnostic evidence."

---

## 4. Search / Memory / Recommendation Logic

### 4.1 Retrieval Mechanism

**Query Lifecycle:**
```
Query → Embed → Qdrant Search → Filter → Rank → [LLM?] → Response
              │              │        │       │
         patient_id      inactive   combined  only if
           filter        excluded    score    evidence
```

**Combined Scoring Formula:**
```python
combined_score = 0.7 × semantic_score + 0.3 × confidence
```

This weights semantic relevance (70%) while respecting memory confidence (30%). High-confidence memories rank higher when semantic scores are similar.

**Evidence Structure:**
```python
@dataclass
class RetrievalEvidence:
    content: str
    semantic_score: float
    confidence: float
    combined_score: float
    source: str
    memory_type: str
    modality: str
    point_id: str
```

### 4.2 Memory Storage and Lifecycle

**Initial Ingestion:**
- New memories start with `confidence: 1.0`
- Each chunk stores `parent_id` for traceability
- Metadata includes `is_active: True` for soft delete support

**Reinforcement (Same Information Repeated):**
When similar content is ingested (cosine similarity > 0.85):
```python
new_confidence = min(current_confidence + 0.15, 1.0)
reinforcement_count += 1
# Duplicate not created—existing memory strengthened
```

This models human memory: repeated information is remembered better.

**Time-Based Decay:**
```python
# Formula: confidence × (0.5 ^ (days_since_last_access / 90))
# Grace period: 7 days (no decay)
# Minimum: 0.1 (never fully forgotten for audit)

decayed_confidence = original × pow(0.5, (days - 7) / 90)
return max(decayed_confidence, 0.1)
```

**Current Status:** Decay function is implemented but requires manual trigger. Scheduled automation (cron job) is not yet configured.

**Soft Delete:**
```python
await memory_manager.soft_delete_memory(
    point_id=memory_id,
    patient_id=patient_id,
    reason="user_requested"
)
# Sets is_active: False, preserves data for audit
# Memory excluded from future searches
```

### 4.3 Anti-Hallucination Control

This is the system's primary safety mechanism:

```python
# In ReasoningChain.reason()
if not evidence:
    return ReasoningResponse(
        answer_text="Insufficient data in patient records...",
        has_context=False,
        evidence_count=0
    )
# LLM is NEVER called when evidence is empty
```

This gate applies to ALL modalities. If retrieval returns nothing across text, document, AND image collections, the system refuses to generate—it returns a fixed safe response.

When evidence exists, the LLM is prompted with explicit grounding rules:
- "Use ONLY the provided evidence"
- "Do NOT introduce facts not present"
- "If insufficient, state 'Insufficient data'"

### 4.4 Follow-Up Suggestions

When evidence exists, the system can generate contextual follow-up questions:

```python
suggestions = await reasoning_chain.suggest_followup_questions(evidence)
# Returns: ["Review recent sleep patterns?", "Check medication adherence?", ...]
```

When no evidence exists, generic safe questions are returned:
```python
return [
    "What is the patient's primary complaint?",
    "Are there any known allergies?",
    "What current medications is the patient taking?"
]
```

---

## 5. Limitations & Ethics

### 5.1 Known Failure Modes

| Failure Mode | Description | Impact |
|--------------|-------------|--------|
| **False Negatives** | Embedding model misses semantic similarity for specialized medical terms | Relevant memories not retrieved |
| **Chunk Boundaries** | Information split across chunks may lose context | Incomplete evidence passed to LLM |
| **Reinforcement Threshold** | 0.85 similarity may incorrectly merge distinct memories | Over-consolidation of different information |
| **LLM Refusal** | Groq may refuse certain medical queries | No answer despite evidence |
| **Cold Start** | New patients have no memories | Generic fallback suggestions only |

### 5.2 Technical Constraints

| Constraint | Status | Notes |
|------------|--------|-------|
| **Authentication** | ❌ Not implemented | API is currently open |
| **Rate Limiting** | ❌ Not implemented | No abuse prevention |
| **OCR for Scanned PDFs** | ❌ Not implemented | Text-based extraction only |
| **Image Diagnosis** | ❌ Explicitly forbidden | By design, not oversight |
| **Audio Support** | ❌ Not implemented | Voice memos not supported |
| **Decay Scheduling** | ⚠️ Manual trigger | Cron job not configured |
| **Hybrid Search** | ❌ Vector only | No BM25/keyword fallback |

### 5.3 Privacy Considerations

**Implemented:**
- Mandatory `patient_id` filter on all Qdrant queries (code-enforced)
- Patient ownership verified before updates/deletes
- Soft delete preserves data for audit while excluding from search
- Demo uses synthetic data only

**Not Implemented:**
- End-to-end encryption
- Audit logging / access trails
- HIPAA-compliant configuration
- User authentication / RBAC
- Patient consent management
- GDPR-style data export/deletion

### 5.4 Bias and Model Limitations

**Embedding Model (all-MiniLM-L6-v2):**
- Trained primarily on English web text
- May underperform on medical jargon, non-English terms, rare conditions
- Semantic similarity ≠ clinical relevance

**LLM (Groq Llama 3.3 70B):**
- May reflect training biases
- No clinical fine-tuning performed
- Cannot reason about information not in evidence
- Responses are summaries, not medical interpretations

**Mitigation Strategies:**
- Confidence scoring surfaces more reliable memories
- Time-based decay reduces stale information impact
- Reinforcement strengthens consistent information
- Anti-hallucination gate prevents generation without evidence

### 5.5 Safety Boundaries

**What This System Does:**
- Organizes and retrieves patient session notes
- Summarizes historical healthcare information
- Provides quick access to past records
- Surfaces relevant context for clinical review

**What This System Does NOT Do:**
- Provide medical diagnosis or treatment recommendations
- Replace clinical judgment of healthcare professionals
- Operate autonomously without human oversight
- Handle emergency medical situations
- Interpret or diagnose from medical images

> **Human-in-the-loop is mandatory.** All outputs include a disclaimer requiring healthcare professional review before clinical decisions.

### 5.6 Explicit Disclaimer

This system is a **prototype for demonstration purposes**.

- It is **not validated for clinical use**
- It has **not undergone regulatory review**
- All demo data is **synthetic**
- Developers are **not responsible** for decisions made based on outputs

**Always consult a qualified healthcare professional for medical decisions.**

---

## Appendix A: Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | Python, FastAPI | 3.11+, 0.128 |
| Vector Database | Qdrant | 1.16 |
| Text Embeddings | FastEmbed (all-MiniLM-L6-v2) | 0.7.4 |
| Image Embeddings | CLIP (ViT-B/32 via Transformers) | — |
| PDF Extraction | PyMuPDF | 1.25 |
| Audio Transcription | Groq Whisper API (whisper-large-v3-turbo) | — |
| LLM | Groq API (Llama 3.3 70B) | — |
| Frontend | Static HTML/CSS/JS | — |
| Deployment | Docker, Docker Compose | — |
| Cloud | Render.com, Qdrant Cloud | — |

---

## Appendix B: API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/memory` | POST | Ingest text memory |
| `/api/v1/memory/document` | POST | Ingest PDF document |
| `/api/v1/memory/image` | POST | Ingest image |
| `/api/v1/memory/audio` | POST | Ingest audio (transcribe + store) |
| `/api/v1/search` | POST | Semantic search (no LLM) |
| `/api/v1/search/context` | POST | Search with LLM-grounded answer |
| `/api/v1/search/multimodal` | POST | Search across all modalities |
| `/api/v1/patient/{id}/summary` | GET | Generate patient summary |
| `/api/v1/patient/{id}/stats` | GET | Memory statistics |
| `/api/v1/patient/{id}/suggestions` | GET | Follow-up question suggestions |
| `/api/v1/health` | GET | Health check |
| `/api/v1/health/ready` | GET | Readiness probe (includes Qdrant) |
| `/api/v1/health/live` | GET | Liveness probe |

---

## Appendix C: Demo Validation

**Anti-Hallucination Proof:**
```bash
# Query about data that does not exist
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","query":"What is the patient blood pressure?"}'

# Response (NO LLM called):
{
  "answer_text": "Insufficient data in patient records...",
  "has_context": false,
  "evidence_count": 0
}
```

**Multimodal Retrieval:**
```bash
# Search across text, documents, and images
curl -X POST http://localhost:8000/api/v1/search/multimodal \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"demo_001","query":"respiratory findings","modalities":["text","document","image"]}'
```

---

*Prepared for Qdrant Convolve 4.0 Hackathon*
