# Demo Flow (Judge Story)

A **5–7 minute demo** showing: problem → memory → retrieval → reasoning → anti-hallucination.

---

## 🧩 Pre-Demo Setup

### Patient
```
patient_id = "patient_001"
```

### Ingest 3 Memories

**Memory 1 — Mental Health Session:**
```json
POST /api/v1/memory
{
  "patient_id": "patient_001",
  "raw_text": "Patient reports feeling anxious, restless, and having trouble sleeping for the past two weeks.",
  "memory_type": "mental_health",
  "source": "session"
}
```

**Memory 2 — Doctor Note:**
```json
POST /api/v1/memory
{
  "patient_id": "patient_001",
  "raw_text": "Prescribed Sertraline 50mg once daily for anxiety management.",
  "memory_type": "medication",
  "source": "doctor"
}
```

**Memory 3 — Follow-up (triggers reinforcement):**
```json
POST /api/v1/memory
{
  "patient_id": "patient_001",
  "raw_text": "Patient reports anxiety symptoms persist, especially at night, but sleep has slightly improved.",
  "memory_type": "mental_health",
  "source": "session"
}
```

---

## 🎬 Demo Steps

### Step 1 — Problem (30s)
> "Healthcare data is fragmented. Systems forget context, and AI hallucinates. We built a memory-first system that only answers using real patient history."

### Step 2 — Ingestion (1min)
- Show `POST /api/v1/memory`
- Point out: chunking, metadata, patient_id isolation
> "Every piece of data becomes long-term memory."

### Step 3 — Evidence Retrieval (1min)
```json
POST /api/v1/search
{"patient_id": "patient_001", "query": "anxiety symptoms"}
```
Show: ranked evidence, confidence scores, timestamps
> **"This is not an answer. This is evidence."**

### Step 4 — Grounded Reasoning (1-2min)
```json
POST /api/v1/search/context
{"patient_id": "patient_001", "query": "What medication was prescribed?"}
```
Highlight: `has_context: true`, `evidence_count`, `sources_used`
> "The model can't invent information. If it's not in memory, it refuses."

### Step 5 — Anti-Hallucination Proof (1min) ⭐
```json
POST /api/v1/search/context
{"patient_id": "patient_001", "query": "What is the patient's blood pressure?"}
```
Response: "Insufficient data", `has_context: false`
> **"This is intentional. Silence is safer than guessing."**

### Step 6 — Evolving Memory (30s)
```
GET /api/v1/patient/patient_001/stats
```
Show: reinforced memories, confidence evolution

---

## 🏁 Closing Line

> "This system doesn't try to be smart — it tries to be **reliable**."

---

## Open During Demo
- Swagger UI (`/docs`)
- Terminal with logs
- Qdrant dashboard (optional)
