# Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- Docker (for Qdrant)
- OpenAI API key

### Quick Start

```bash
# 1. Clone and setup
cd healthcare-memory-assistant
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# 3. Start Qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# 4. Initialize collections
python scripts/init_collections.py

# 5. Run the API
uvicorn app.main:app --reload
```

## Docker Deployment

### Full Stack (App + Qdrant)

```bash
cd docker
docker-compose up -d
```

### Build Only

```bash
docker build -t healthcare-memory-assistant -f docker/Dockerfile .
```

## Cloud Deployment

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `QDRANT_HOST` | Yes | Qdrant server hostname |
| `QDRANT_PORT` | Yes | Qdrant server port |
| `GROQ_API_KEY` | Yes | Groq API key |
| `API_KEY_SECRET` | Yes | API authentication key |


### Qdrant Cloud

1. Create a cluster at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Set `QDRANT_HOST` to your cluster URL
3. Set `QDRANT_API_KEY` to your API key

### Recommended Stack (Best for this Project)

**1. Backend: Render**
- **Why**: Excellent Python support, free tier, and we have already created the `render.yaml` blueprint for one-click setup.
- **Cost**: Free (spins down after inactivity) or $7/mo for always-on.

**2. Frontend: Vercel**
- **Why**: Best-in-class for static content (`index.html`), global CDN, and zero-config deployment.
- **Cost**: Free.

**3. Database: Qdrant Cloud**
- **Why**: The free tier covers up to 1GB of vectors, which is plenty for this project. Docker on Render free tier does not have persistent storage, so you **must** use Qdrant Cloud for data to survive restarts.

### Other Options
- **Railway**: Great alternative if you want the backend + database in one place. Easy setup but no permanent free tier (credits system).
- **AWS/Google**: Overkill for a personal project. Too much configuration maintenance.

## Health Checks

- Liveness: `GET /api/v1/health/live`
- Readiness: `GET /api/v1/health/ready`

## Scaling Considerations

1. **Qdrant**: Use Qdrant Cloud for production
2. **Embeddings**: Consider caching frequent queries
3. **LLM Calls**: Implement rate limiting
