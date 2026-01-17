# Architecture Documentation

## System Overview

The Healthcare Memory Assistant is a multi-patient memory system that uses semantic embeddings to store and retrieve healthcare-related memories.

### Key Design Principles

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) | Local semantic encoding |
| **Vector DB** | Qdrant | Long-term memory storage |
| **LLM** | OpenAI GPT-4 | Reasoning & response generation |

> **Hallucination Control**: If no relevant memory is retrieved from Qdrant, the system explicitly responds with "insufficient data" instead of generating an answer.

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Memory  │  │ Search  │  │ Patient │  │ Health  │    │
│  │Endpoint │  │Endpoint │  │Endpoint │  │Endpoint │    │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────────┘    │
└───────┼────────────┼────────────┼───────────────────────┘
        │            │            │
        ▼            ▼            ▼
┌─────────────────────────────────────────────────────────┐
│                   Memory Manager                         │
│              (Orchestration Layer)                       │
└───────┬────────────┬────────────┬───────────────────────┘
        │            │            │
        ▼            ▼            ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│ Embedding │  │ Retrieval │  │ Reasoning │
│  Engine   │  │  Engine   │  │  (LLM)    │
└─────┬─────┘  └─────┬─────┘  └───────────┘
      │              │
      └──────┬───────┘
             ▼
┌─────────────────────────────────────────────────────────┐
│                  Qdrant Vector DB                        │
│              (Primary Long-term Memory)                  │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Memory Storage
1. Client sends memory content
2. API validates request
3. Preprocessor cleans text
4. Embedder generates vector
5. Qdrant stores vector + metadata

### Memory Retrieval
1. Client sends search query
2. Query is embedded
3. Qdrant performs similarity search
4. Results are filtered by patient_id
5. Optional: LLM generates summary

## Key Design Decisions

1. **Patient Isolation**: All queries filter by `patient_id`
2. **Qdrant-First**: Vector DB is non-replaceable core
3. **Modular Services**: Each module is independently testable
4. **Async by Default**: All I/O operations are async
