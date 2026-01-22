# Healthcare Memory Assistant

A memory-first AI system for healthcare decision support with zero-hallucination design.

**Built for Qdrant Convolve 4.0 Hackathon**

---

## Quick Start (5 minutes)

### Prerequisites

- Python 3.11+
- [Groq API Key](https://console.groq.com/) (free tier available)
- [Qdrant Cloud Account](https://cloud.qdrant.io/) (free tier available) OR Docker

### Option A: Qdrant Cloud (Recommended)

**Step 1: Clone and setup environment**

```bash
git clone <repo-url>
cd Quadrant

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Step 2: Configure environment variables**

```bash
# Copy example env file
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Qdrant Cloud (get from https://cloud.qdrant.io)
QDRANT_URL=https://your-cluster-id.region.qdrant.cloud
QDRANT_API_KEY=your_qdrant_api_key_here
```

**Step 3: Initialize Qdrant collections**

```bash
python scripts/init_collections.py
```

You should see:
```
✓ Collection: patient_memories (384-dim)
✓ Collection: patient_images (512-dim)
```

**Step 4: Start the backend**

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 5: Start the frontend** (new terminal)

```bash
cd frontend
python -m http.server 3000
```

**Step 6: Open the app**

- Frontend Dashboard: http://localhost:3000/dashboard.html
- API Documentation: http://localhost:8000/docs

---

### Option B: Local Docker (No Cloud Required)

**Step 1: Clone and setup**

```bash
git clone <repo-url>
cd Quadrant
```

**Step 2: Start with Docker Compose**

```bash
# Copy env file
cp .env.example .env

# Add your Groq API key to .env
# GROQ_API_KEY=your_key_here

# Start all services
docker-compose up --build
```

**Step 3: Initialize collections**

```bash
docker exec healthcare-backend python scripts/init_collections.py
```

**Step 4: Access the app**

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

---

## Verify It's Working

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status": "healthy", "qdrant": "connected"}
```

### 2. Add a Test Memory

```bash
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "test_patient",
    "raw_text": "Patient reports anxiety and trouble sleeping.",
    "memory_type": "mental_health",
    "source": "session"
  }'
```

### 3. Search for It

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "test_patient",
    "query": "sleep problems"
  }'
```

### 4. Test Anti-Hallucination

```bash
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "test_patient",
    "query": "What is the blood pressure?"
  }'
```

Expected: `"Insufficient data in patient records..."` (LLM was never called)

---

## Load Demo Data (Optional)

To populate the system with synthetic patient data for testing:

```bash
python scripts/load_demo_data.py
```

This creates sample patients with session notes, medications, and clinical observations.

---

## Project Structure

```
Quadrant/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── api/v1/              # REST endpoints
│   ├── memory/              # Ingestion, reinforcement, decay
│   ├── retrieval/           # Semantic search engine
│   ├── reasoning/           # LLM prompting, anti-hallucination
│   ├── embedding/           # Text embeddings (MiniLM)
│   ├── multimodal/          # PDF, audio, image processors
│   └── db/                  # Qdrant operations
├── frontend/
│   ├── index.html           # Landing page
│   └── dashboard.html       # Main application UI
├── scripts/
│   ├── init_collections.py  # Setup Qdrant collections
│   └── load_demo_data.py    # Load synthetic data
├── docs/
│   ├── HACKATHON_SUBMISSION.md
│   └── DEMO_VIDEO_SCRIPT.md
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/memory` | POST | Ingest text memory |
| `/api/v1/memory/document` | POST | Ingest PDF document |
| `/api/v1/memory/audio` | POST | Ingest audio (transcribe + store) |
| `/api/v1/memory/image` | POST | Ingest image |
| `/api/v1/search` | POST | Semantic search (no LLM) |
| `/api/v1/search/context` | POST | Search with LLM-grounded answer |
| `/api/v1/patient/{id}/summary` | GET | Generate patient summary |
| `/api/v1/patient/{id}/stats` | GET | Memory statistics |

Full API documentation available at http://localhost:8000/docs

---

## Key Features

- **Semantic Search**: Find memories by meaning, not keywords
- **Anti-Hallucination Gate**: No evidence = no LLM call = no fabrication
- **Multimodal**: Text, PDFs, audio transcription, images
- **Memory Evolution**: Reinforcement (+0.15) for repeated info, decay over time
- **Patient Isolation**: Every query filtered by patient_id

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11, FastAPI |
| Vector DB | Qdrant 1.16 |
| Text Embeddings | FastEmbed (MiniLM, 384-dim) |
| Image Embeddings | CLIP ViT-B/32 (512-dim) |
| Audio | Groq Whisper API |
| LLM | Groq (Llama 3.3 70B) |
| PDF | PyMuPDF |

---

## Troubleshooting

### "Collection doesn't exist" error

Run the initialization script:
```bash
python scripts/init_collections.py
```

### "GROQ_API_KEY not configured" error

Make sure your `.env` file contains:
```
GROQ_API_KEY=your_actual_key_here
```

### Qdrant connection refused

If using Docker, ensure Qdrant container is running:
```bash
docker-compose up qdrant
```

If using Qdrant Cloud, verify your `QDRANT_URL` and `QDRANT_API_KEY` in `.env`.

### Port already in use

Change the port:
```bash
# Backend
python -m uvicorn app.main:app --port 8001

# Frontend
python -m http.server 3001
```

---

## Limitations

- No user authentication (hackathon scope)
- No OCR for scanned PDFs
- Not HIPAA/GDPR compliant
- Demo uses synthetic data only

---

## License

MIT

---

*Built for Qdrant Convolve 4.0 Hackathon. All demo data is synthetic.*
