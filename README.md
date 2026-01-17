# Healthcare & Mental Health Memory Assistant

A memory-first AI system for healthcare decision support with **zero hallucination**.

> "This system doesn't try to be smart — it tries to be **reliable**."

---

## ✨ Key Features

- **Long-term memory** — Patient data stored as semantic embeddings in Qdrant
- **Evidence-based reasoning** — LLM answers grounded in retrieved memories
- **Anti-hallucination** — No evidence = no answer (LLM not called)
- **Evolving memory** — Confidence reinforcement and time-based decay
- **Patient isolation** — All queries scoped to `patient_id`

---

## 🚀 Run Locally (One Command)

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### Steps

```bash
# 1. Clone and navigate
git clone <repo-url>
cd Quadrant

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start everything
docker-compose up --build

# 4. Initialize Qdrant collection
docker exec healthcare-backend python scripts/init_collections.py
```

### Access
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## ☁️ Deploy to Cloud

### Option 1: Qdrant Cloud + Any Container Platform

**Step 1: Use Qdrant Cloud**
1. Create account at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a cluster
3. Get your URL and API key

**Step 2: Update environment**
```env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

**Step 3: Deploy backend to any platform**
- Render, Railway, Fly.io, AWS ECS, Google Cloud Run
- No code changes needed — just set environment variables

### Option 2: Full Docker on Cloud VM

```bash
# On your VM
docker-compose up -d
```

---

## 🎬 Demo Steps for Judges

### Quick Test (2 minutes)

**1. Ingest a memory:**
```bash
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","raw_text":"Patient reports anxiety and trouble sleeping.","memory_type":"mental_health","source":"session"}'
```

**2. Search memories:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","query":"anxiety symptoms"}'
```

**3. Get grounded answer:**
```bash
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","query":"What symptoms were reported?"}'
```

**4. Prove anti-hallucination:**
```bash
curl -X POST http://localhost:8000/api/v1/search/context \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient_001","query":"What is the blood pressure?"}'
```
→ Returns "Insufficient data" (no hallucination!)

### Full Demo Flow
See [docs/DEMO_FLOW.md](docs/DEMO_FLOW.md) for the complete 5-7 minute judge demo.

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│   Retrieval  │────▶│   Qdrant    │
│   (API)     │     │   Engine     │     │  (Vectors)  │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│  Reasoning  │◀────│   Evidence   │
│   (LLM)     │     │   (Memory)   │
└─────────────┘     └──────────────┘
```

- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384-dim, local)
- **LLM**: OpenAI GPT-4 (for reasoning only)
- **Vector DB**: Qdrant (Cosine similarity)

---

## 📁 Project Structure

```
Quadrant/
├── app/
│   ├── api/v1/          # FastAPI endpoints
│   ├── db/              # Qdrant operations
│   ├── embedding/       # Embedder, chunker, preprocessor
│   ├── memory/          # Ingestion, reinforcement, decay
│   ├── retrieval/       # Semantic search, ranking
│   └── reasoning/       # LLM, prompts, chains
├── docs/                # Documentation
├── scripts/             # Init, seed scripts
├── docker-compose.yml   # One-command deployment
└── Dockerfile           # Production container
```

---

## 📚 Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Ethics & Safety](docs/ETHICS_AND_SAFETY.md)
- [Demo Flow](docs/DEMO_FLOW.md)

---

## ⚠️ Disclaimer

This is a **prototype for demonstration purposes**. Not validated for clinical use. Always consult healthcare professionals for medical decisions.

---

## 📝 License

MIT
