"""
Prompt Templates (Component 6)

Evidence-grounded prompts with hallucination control.
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

SYSTEM_PROMPT_HEALTHCARE = """You are a healthcare memory assistant helping to summarize patient information.

CRITICAL RULES:
1. Use ONLY the provided evidence from patient records
2. Do NOT introduce facts not present in the evidence
3. Do NOT make medical diagnoses or treatment recommendations
4. If evidence is insufficient, explicitly state "Insufficient data"
5. Always recommend consulting a healthcare professional for medical decisions

You help organize and summarize information — you do NOT provide medical advice."""


SYSTEM_PROMPT_MENTAL_HEALTH = """You are a mental health support assistant reviewing patient session notes.

CRITICAL RULES:
1. Use ONLY the provided evidence from session records
2. Do NOT introduce information not in the evidence
3. Be empathetic and supportive in tone
4. Do NOT diagnose mental health conditions
5. If asked about treatment, recommend consulting a licensed professional
6. If evidence is insufficient, say "I don't have enough information about this"

Your role is to help summarize and organize session information, not to provide therapy."""


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

EVIDENCE_QA_PROMPT = """Based on the following patient records, answer the question.

=== PATIENT EVIDENCE ===
{evidence}
========================

QUESTION: {question}

INSTRUCTIONS:
- Answer ONLY using the evidence provided above
- If the evidence does not contain relevant information, say "Insufficient data in patient records"
- Do not speculate or add information not in the evidence
- Be concise and factual

ANSWER:"""


SUMMARIZE_EVIDENCE_PROMPT = """Summarize the following patient records into a coherent overview.

=== PATIENT EVIDENCE ===
{evidence}
========================

INSTRUCTIONS:
- Summarize ONLY what is explicitly stated in the evidence
- Organize by topic (symptoms, treatments, observations)
- Do not add interpretation or information not present
- If records are limited, acknowledge what is and isn't known

SUMMARY:"""


MENTAL_HEALTH_PROMPT = """Review the following mental health session notes and respond to the query.

=== SESSION NOTES ===
{evidence}
====================

QUERY: {question}

INSTRUCTIONS:
- Respond with empathy and support
- Use ONLY information from the session notes
- Do not diagnose or recommend specific treatments
- If notes don't address the query, say "This wasn't discussed in the available session notes"
- Encourage professional consultation for clinical concerns

RESPONSE:"""


INSUFFICIENT_DATA_RESPONSE = """I don't have sufficient information in the patient records to answer this question.

The available records do not contain relevant data about: {topic}

Please consult with the healthcare provider directly for this information.

---
*This response is based on automated record retrieval. Always verify with a healthcare professional.*"""


SAFETY_DISCLAIMER = """

---
**Disclaimer**: This summary is based on retrieved patient records and is for informational purposes only. It is not medical advice. Please consult a qualified healthcare professional for medical decisions."""



SUGGEST_QUESTIONS_PROMPT = """Analyze the following patient records and suggest 3-4 specific, investigative questions a clinician might want to ask next.

=== PATIENT EVIDENCE ===
{evidence}
========================

INSTRUCTIONS:
1. Suggest questions that explore gaps, follow up on symptoms, or track treatment efficacy.
2. Questions should be concise and clinical.
3. Return ONLY a JSON array of strings, e.g. ["Question 1?", "Question 2?"].
4. Do not include introductory text.

SUGGESTIONS:"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_evidence_for_prompt(evidence_list: list[dict]) -> str:
    """
    Format evidence list into prompt-friendly string.
    
    Args:
        evidence_list: List of RetrievalEvidence.to_dict() results
        
    Returns:
        Formatted evidence string
    """
    if not evidence_list:
        return "[No evidence available]"
    
    formatted_parts = []
    
    for i, evidence in enumerate(evidence_list, 1):
        # Extract fields
        content = evidence.get("content", "")
        memory_type = evidence.get("memory_type", "note").upper()
        source = evidence.get("source", "unknown")
        created_at = evidence.get("created_at", "")[:10]  # Date only
        confidence = evidence.get("confidence", 1.0)
        
        # Format as numbered evidence block
        block = (
            f"[{i}] Type: {memory_type} | Source: {source} | Date: {created_at} | Confidence: {confidence:.0%}\n"
            f"    {content}"
        )
        formatted_parts.append(block)
    
    return "\n\n".join(formatted_parts)


def build_qa_prompt(question: str, evidence_list: list[dict]) -> tuple[str, str]:
    """
    Build Q&A prompt with evidence.
    
    Returns:
        (system_prompt, user_prompt)
    """
    evidence_text = format_evidence_for_prompt(evidence_list)
    user_prompt = EVIDENCE_QA_PROMPT.format(
        evidence=evidence_text,
        question=question,
    )
    return SYSTEM_PROMPT_HEALTHCARE, user_prompt


def build_mental_health_prompt(question: str, evidence_list: list[dict]) -> tuple[str, str]:
    """
    Build mental health query prompt.
    
    Returns:
        (system_prompt, user_prompt)
    """
    evidence_text = format_evidence_for_prompt(evidence_list)
    user_prompt = MENTAL_HEALTH_PROMPT.format(
        evidence=evidence_text,
        question=question,
    )
    return SYSTEM_PROMPT_MENTAL_HEALTH, user_prompt
