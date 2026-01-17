# Healthcare Memory Assistant - API Documentation

## Overview

The Healthcare Memory Assistant provides a RESTful API for storing and retrieving patient memories using semantic search powered by Qdrant vector database.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All protected endpoints require an API key in the header:

```
X-API-Key: your-api-key
```

## Endpoints

### Health Check

#### GET /health
Basic health check.

**Response:**
```json
{"status": "healthy"}
```

#### GET /health/ready
Readiness check including Qdrant status.

#### GET /health/live
Liveness probe for Kubernetes.

---

### Memory Management

#### POST /memory
Store a new memory.

**Request Body:**
```json
{
  "patient_id": "patient_001",
  "content": "Patient reported headache for 3 days",
  "memory_type": "clinical",
  "source": "session",
  "metadata": {}
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "patient_id": "patient_001",
  "content": "...",
  "memory_type": "clinical",
  "source": "session",
  "created_at": "2024-01-01T00:00:00Z",
  "metadata": {}
}
```

#### GET /memory/{patient_id}
Get all memories for a patient.

**Query Parameters:**
- `limit` (int): Max results (default: 100)

#### DELETE /memory/{memory_id}
Delete a specific memory.

---

### Semantic Search

#### POST /search
Search memories semantically.

**Request Body:**
```json
{
  "patient_id": "patient_001",
  "query": "headache symptoms",
  "limit": 10,
  "min_score": 0.5,
  "memory_types": ["clinical", "symptom"]
}
```

#### POST /search/context
Search with LLM-generated summary.

---

### Patient Insights

#### GET /patient/{patient_id}/summary
Get AI-generated patient summary.

#### GET /patient/{patient_id}/mental-health
Get mental health insights.

#### GET /patient/{patient_id}/stats
Get memory statistics.

---

## Memory Types

| Type | Description |
|------|-------------|
| `clinical` | Medical/clinical observations |
| `mental_health` | Mental health related |
| `medication` | Medication history |
| `lifestyle` | Lifestyle information |
| `symptom` | Reported symptoms |
| `appointment` | Appointment records |
| `general` | General notes |

## Error Responses

```json
{
  "detail": "Error message"
}
```

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Server Error |
