# Ethics, Safety, and Limitations

## Intended Use

This Healthcare Memory Assistant is designed as a **decision support tool**, not a diagnostic or treatment system.

**Intended for:**
- Organizing and retrieving patient session notes
- Summarizing historical healthcare information
- Supporting healthcare professionals with quick access to past records
- Mental health practitioners reviewing session history

**NOT intended for:**
- Medical diagnosis or treatment recommendations
- Replacing clinical judgment of healthcare professionals
- Autonomous patient care without human oversight
- Emergency medical situations

> **Human-in-the-loop is mandatory.** All outputs should be reviewed by a qualified healthcare professional before any clinical decisions.

---

## Safety Measures

### Hallucination Control
| Mechanism | Implementation |
|-----------|----------------|
| No evidence = No LLM | If retrieval returns empty, system returns fixed "insufficient data" response without calling LLM |
| Evidence-only prompts | LLM explicitly instructed to use ONLY provided evidence |
| Confidence thresholds | Low-confidence memories weighted lower in ranking |

### Evidence-Based Reasoning
- All generated answers cite retrieved memories
- `has_context: false` flag clearly indicates when no evidence was available
- Sources and evidence counts included in every response

### Audit Trail
- **Soft delete**: Memories marked inactive, never fully erased
- All updates timestamped with `updated_at`
- Chunk traceability via `parent_id` and `chunk_index`

### Patient Isolation
- All queries **require** `patient_id` parameter
- Cross-patient access attempts raise errors
- Database queries always filter by patient scope

---

## Privacy & Data Handling

### Data Scoping
- Each patient's memories stored with mandatory `patient_id`
- No global queries across patients
- All operations enforce patient isolation at application layer

### Demo Assumptions
- This system uses **synthetic/demo data** for development
- No real patient data is included or expected during hackathon evaluation

### Production Requirements (Future)
- Data encryption at rest and in transit
- HIPAA/GDPR compliance review required
- PHI anonymization before storage
- Access logging and consent management

---

## Bias & Model Limitations

### Embedding Model Limitations
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Trained primarily on English text
- May underperform on medical jargon, non-English terms, or rare conditions
- Semantic similarity ≠ clinical relevance

### LLM Limitations
- May misinterpret ambiguous medical terminology
- Cannot reason about information not in evidence
- Responses are summaries, not medical interpretations

### Mitigation Strategies
| Risk | Mitigation |
|------|-----------|
| Model bias | Confidence scoring surfaces reliable memories |
| Stale information | Time-based decay reduces confidence of old, unused memories |
| Repeated errors | Reinforcement strengthens consistent information |
| Hallucination | No-LLM-if-no-evidence policy |

---

## Failure Modes

### When the System May Fail
- No relevant memories match the query
- Embedding quality is poor for specialized medical terms
- LLM misinterprets evidence despite constraints
- Network/service interruption (Qdrant, OpenAI)

### Safe Failure Responses
| Failure | Response |
|---------|----------|
| No evidence found | `"Insufficient data in patient records"` (no LLM called) |
| LLM error | HTTP 500 with clear error message |
| Invalid patient_id | HTTP 400 with validation error |
| Qdrant unavailable | Health check reports `"degraded"` |

### User Guidance
- If system returns "insufficient data," consult records directly
- Never rely solely on system output for clinical decisions
- Report unexpected outputs to development team

---

## Limitations & Future Work

### Intentionally Out of Scope (Hackathon)
- User authentication and authorization
- Multi-tenant organization support
- Real-time streaming of responses
- Fine-tuned medical embeddings
- Regulatory compliance (HIPAA, GDPR)

### Production Improvements
- [ ] Fine-tuned embedding model for healthcare terminology
- [ ] Reranking with medical cross-encoders
- [ ] User feedback loop for reinforcement
- [ ] Automated decay scheduling (cron jobs)
- [ ] Comprehensive logging and monitoring
- [ ] Role-based access control

---

## Disclaimer

> This system is a prototype for educational and demonstration purposes. It is **not validated for clinical use**. Any resemblance to real patient data is coincidental. The developers are not responsible for decisions made based on system outputs.

**Always consult a qualified healthcare professional for medical decisions.**
