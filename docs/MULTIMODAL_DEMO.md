# Multimodal Demo Validation Guide

Demonstrates multimodal retrieval across text, document, and image modalities.

## Demo Patient
- **Patient ID**: `demo_multimodal_001`

## Sample Data Loaded

| Modality | Content | Source |
|----------|---------|--------|
| TEXT | Clinical notes (cough, fatigue) | session |
| TEXT | Medication (amoxicillin 500mg) | doctor |
| TEXT | Mental health (improved mood) | session |
| DOCUMENT | Lab report (CBC - all normal) | pdf |
| IMAGE | Chest X-ray reference | upload |

---

## Example Queries & Expected Responses

### 1. Text-Only Retrieval

**Query**: "What medications was the patient prescribed?"

**API Call**:
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "demo_multimodal_001",
    "query": "What medications was the patient prescribed?",
    "modalities": ["text"]
  }'
```

**Expected Response**:
```json
{
  "query": "What medications was the patient prescribed?",
  "patient_id": "demo_multimodal_001",
  "total_found": 1,
  "evidence": [
    {
      "content": "Prescribed amoxicillin 500mg TID for 7 days...",
      "modality": "text",
      "memory_type": "medication",
      "source": "doctor",
      "semantic_score": 0.85,
      "combined_score": 0.89
    }
  ]
}
```

---

### 2. Document-Only Retrieval

**Query**: "What were the lab test results?"

**API Call**:
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "demo_multimodal_001",
    "query": "What were the lab test results?",
    "modalities": ["document"]
  }'
```

**Expected Response**:
```json
{
  "query": "What were the lab test results?",
  "patient_id": "demo_multimodal_001",
  "total_found": 1,
  "evidence": [
    {
      "content": "LABORATORY REPORT - COMPLETE BLOOD COUNT... All values within normal limits.",
      "modality": "document",
      "memory_type": "clinical",
      "source": "pdf",
      "semantic_score": 0.82,
      "combined_score": 0.87
    }
  ]
}
```

---

### 3. Image-Only Retrieval

**Query**: "Show chest imaging"

**API Call**:
```bash
curl -X POST http://localhost:8000/api/v1/search/multimodal \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "demo_multimodal_001",
    "query": "chest imaging",
    "modalities": ["image"]
  }'
```

**Expected Response**:
```json
{
  "query": "chest imaging",
  "patient_id": "demo_multimodal_001",
  "total_found": 1,
  "evidence": [
    {
      "content": "[IMAGE: chest_xray_2026_01_10.jpg] Chest X-ray anterior-posterior view",
      "modality": "image",
      "memory_type": "clinical",
      "source": "upload",
      "image_filename": "chest_xray_2026_01_10.jpg",
      "image_width": 1024,
      "image_height": 768,
      "semantic_score": 0.75,
      "combined_score": 0.82
    }
  ]
}
```

---

### 4. Combined Multimodal Retrieval

**Query**: "Summarize respiratory findings"

**API Call**:
```bash
curl -X POST http://localhost:8000/api/v1/search/multimodal \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "demo_multimodal_001",
    "query": "respiratory findings",
    "modalities": ["text", "document", "image"]
  }'
```

**Expected Response** (combined from all modalities):
```json
{
  "query": "respiratory findings",
  "patient_id": "demo_multimodal_001",
  "total_found": 3,
  "modalities_found": ["text", "document", "image"],
  "evidence": [
    {
      "content": "Patient presents with persistent cough for 2 weeks...",
      "modality": "text",
      "memory_type": "clinical",
      "combined_score": 0.88
    },
    {
      "content": "Prescribed amoxicillin 500mg TID for 7 days for suspected upper respiratory infection...",
      "modality": "text",
      "memory_type": "medication",
      "combined_score": 0.85
    },
    {
      "content": "[IMAGE: chest_xray_2026_01_10.jpg] Chest X-ray anterior-posterior view",
      "modality": "image",
      "memory_type": "clinical",
      "image_filename": "chest_xray_2026_01_10.jpg",
      "combined_score": 0.78
    }
  ]
}
```

---

## Anti-Hallucination Validation

### Test: Empty Evidence Returns Fixed Response

**Query**: "What about cardiac history?" (no data exists)

**Expected Response** (NO LLM called):
```json
{
  "answer_text": "Insufficient data in patient records to answer this question. No relevant memories were found.",
  "has_context": false,
  "evidence_count": 0,
  "sources_used": [],
  "disclaimer": "No patient records matched this query."
}
```

✅ Confirms: LLM is NOT called when evidence is empty across ALL modalities.

---

## Running the Demo

```bash
# 1. Initialize collections (if not done)
python scripts/init_collections.py

# 2. Load multimodal demo data
python scripts/load_multimodal_demo.py

# 3. Start the server
uvicorn app.main:app --reload

# 4. Run example queries (above)
```
