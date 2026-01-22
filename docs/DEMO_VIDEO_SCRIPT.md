# Healthcare Memory Assistant — Demo Video Script

**Target Duration: 4-5 minutes**

---

## SCENE 1: Hook (0:00 - 0:20)

**[Screen: Problem statement slide or dashboard]**

> "Healthcare providers face a dangerous problem: patient information is scattered across time.
>
> A psychiatrist seeing a patient today might need to recall something mentioned three months ago. With 30+ patients, that's humanly impossible.
>
> AI can help—but it introduces a new risk: **hallucination**. A fabricated fact in healthcare isn't just wrong. It's dangerous.
>
> We built a system that refuses to guess. Let me show you."

---

## SCENE 2: System Overview (0:20 - 0:45)

**[Screen: Architecture diagram or dashboard overview]**

> "This is the Healthcare Memory Assistant.
>
> It stores patient memories as semantic embeddings in **Qdrant**. When a clinician asks a question, it searches for relevant evidence. If evidence exists, it summarizes. If not, it stays silent.
>
> The key insight: **Qdrant is the brain. The LLM is just the translator.**
>
> Let me walk you through the core features."

---

## SCENE 3: Text Ingestion (0:45 - 1:15)

**[Screen: Dashboard → Ingest Panel → Text tab]**

**ACTION:** Type in Patient ID: `demo_patient_001`

**ACTION:** Enter session note:
```
Patient reports increased anxiety over the past two weeks. 
Having trouble sleeping, waking up at 3am most nights. 
Mentioned work stress as a trigger. 
Currently taking sertraline 50mg daily.
```

**ACTION:** Click "Ingest Memory"

> "Here I'm adding a session note. The system:
> 1. Chunks the text into segments
> 2. Generates embeddings using MiniLM
> 3. Stores in Qdrant with the patient ID
>
> Every memory is automatically tagged with confidence, timestamp, and modality."

**[Show success response]**

---

## SCENE 4: Semantic Search (1:15 - 1:45)

**[Screen: Search Panel]**

**ACTION:** Enter Patient ID: `demo_patient_001`

**ACTION:** Search query: `sleep problems`

**ACTION:** Click "Search"

> "Now let's search. I'm asking about 'sleep problems'—but the note said 'trouble sleeping' and 'waking at 3am'.
>
> **Keyword search would miss this. Semantic search finds it.**
>
> Notice the combined score: 70% semantic similarity, 30% confidence weighting. Recent, reinforced memories rank higher."

**[Show search results with scores]**

---

## SCENE 5: Grounded Reasoning (1:45 - 2:30)

**[Screen: Search Panel → Context Search tab]**

**ACTION:** Enter query: `What symptoms has the patient reported recently?`

**ACTION:** Click "Search with Context"

> "This is where it gets powerful. I'm asking a question that requires synthesis.
>
> The system:
> 1. Retrieves relevant memories from Qdrant
> 2. Passes them as evidence to the LLM
> 3. The LLM summarizes—using **only** that evidence
>
> Every answer includes a disclaimer and cites its sources."

**[Show LLM response with evidence citations]**

---

## SCENE 6: Anti-Hallucination Demo (2:30 - 3:00)

**[Screen: Search Panel → Context Search]**

**ACTION:** Enter query: `What is the patient's blood pressure?`

**ACTION:** Click "Search with Context"

> "Now watch this. I'm asking about blood pressure—but we never recorded that.
>
> **The system returns 'Insufficient data.'**
>
> This is the core safety mechanism. When Qdrant returns no relevant memories, the LLM is **never called**. No evidence, no generation, no hallucination.
>
> In healthcare, 'I don't know' is the safe answer."

**[Show "Insufficient data" response]**

---

## SCENE 7: Multimodal — PDF Document (3:00 - 3:30)

**[Screen: Ingest Panel → Document tab]**

**ACTION:** Upload a sample PDF (e.g., referral letter)

> "The system handles more than text. Here I'm uploading a PDF referral letter.
>
> It extracts text using PyMuPDF, chunks it, and embeds it alongside session notes.
>
> One query can now retrieve typed notes AND documents together."

**[Show successful document ingestion]**

**[Optional: Search and show document appearing in results]**

---

## SCENE 8: Multimodal — Audio (3:30 - 3:50)

**[Screen: Ingest Panel → Audio tab]**

**ACTION:** Upload a short audio file (or describe the flow)

> "For audio, the system transcribes using Groq Whisper, then embeds the transcript.
>
> Session recordings become searchable memories—no manual transcription needed."

---

## SCENE 9: Multimodal — Image (3:50 - 4:10)

**[Screen: Ingest Panel → Image tab]**

**ACTION:** Upload a clinical image

> "Images use a separate embedding model—CLIP. They're stored in their own Qdrant collection.
>
> Important: **We don't analyze or diagnose from images.** They're stored as contextual references only. The LLM is explicitly told not to interpret them."

**[Show successful image ingestion]**

---

## SCENE 10: Memory Reinforcement (4:10 - 4:25)

**[Screen: Ingest Panel]**

**ACTION:** Ingest a similar note to the first one:
```
Patient continues to report sleep difficulties. Still waking early.
```

> "When I add a similar memory, the system doesn't duplicate. It **reinforces** the existing memory—boosting its confidence score by 0.15.
>
> Repeated information ranks higher. This models how human memory works."

**[Show "reinforced" response instead of "created"]**

---

## SCENE 11: Patient Isolation (4:25 - 4:40)

**[Screen: Search Panel]**

**ACTION:** Change Patient ID to `different_patient_002`

**ACTION:** Search for `sleep problems`

> "Every query filters by patient ID. If I switch to a different patient, I see nothing.
>
> **Cross-patient data access is architecturally impossible.** This is enforced at the database layer, not just application code."

**[Show empty results]**

---

## SCENE 12: Closing (4:40 - 5:00)

**[Screen: Dashboard overview or architecture diagram]**

> "To recap:
>
> - **Qdrant** stores semantic memories with confidence scores
> - **Patient isolation** is mandatory on every query
> - **Anti-hallucination gate** prevents the LLM from generating without evidence
> - **Multimodal support** for text, documents, audio, and images
> - **Memory evolution** through reinforcement and decay
>
> This is the Healthcare Memory Assistant. An AI that refuses to guess.
>
> Thank you."

---

## B-ROLL SUGGESTIONS

- Qdrant Cloud dashboard showing collections
- API docs at `/docs` endpoint
- Terminal showing backend startup
- Code snippet of the anti-hallucination gate
- Architecture diagram animation

---

## KEY DEMO DATA TO PREPARE

Before recording, ingest these memories for `demo_patient_001`:

1. **Session note about anxiety and sleep**
2. **Medication note about sertraline**
3. **PDF referral letter (optional)**
4. **One image (optional)**

This ensures all searches return meaningful results during the demo.

---

## TIPS FOR RECORDING

- **Pause briefly** after each action so viewers can follow
- **Keep your voice calm and clear** — clinical tone fits the healthcare context
- **Highlight the "Insufficient data" response** — this is the key differentiator
- **Show the combined scores** to demonstrate Qdrant's role
- **End strong** on the anti-hallucination message

---

*Total runtime: 4-5 minutes*
