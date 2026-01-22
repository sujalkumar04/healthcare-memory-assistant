"""
Reasoning Pipeline (Component 6)

Evidence-grounded response generation with hallucination control.
"""

from dataclasses import dataclass, asdict
from typing import Any

from app.reasoning.llm import llm_client
from app.reasoning.prompts import (
    SYSTEM_PROMPT_HEALTHCARE,
    SYSTEM_PROMPT_MENTAL_HEALTH,
    EVIDENCE_QA_PROMPT,
    MENTAL_HEALTH_PROMPT,
    SUMMARIZE_EVIDENCE_PROMPT,
    INSUFFICIENT_DATA_RESPONSE,
    SAFETY_DISCLAIMER,
    format_evidence_for_prompt,
)


# =============================================================================
# RESPONSE STRUCTURES
# =============================================================================

@dataclass
class ReasoningResponse:
    """
    Structured response from reasoning pipeline.
    
    Separates:
    - What is known (answer from evidence)
    - What cannot be concluded (limitations)
    """
    answer_text: str
    has_context: bool
    evidence_count: int
    sources_used: list[str]
    disclaimer: str
    
    # Metadata
    query: str
    patient_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Fixed response when no evidence is available
NO_EVIDENCE_RESPONSE = ReasoningResponse(
    answer_text="Insufficient data in patient records to answer this question. No relevant memories were found.",
    has_context=False,
    evidence_count=0,
    sources_used=[],
    disclaimer="No patient records matched this query. Please consult with the healthcare provider directly.",
    query="",
    patient_id="",
)


# =============================================================================
# REASONING CHAINS
# =============================================================================

class ReasoningChain:
    """
    Evidence-grounded reasoning pipeline.
    
    ==========================================================================
    ANTI-HALLUCINATION CONTROL (CRITICAL - APPLIES TO ALL MODALITIES)
    ==========================================================================
    
    This safeguard ensures NO LLM generation without evidence:
    
    1. If evidence list is empty → return FIXED safe response (NO LLM call)
    2. This applies to ALL modalities: text, document, AND image
    3. If evidence exists → construct prompt with explicit grounding rules
    4. LLM instructed to say "Insufficient data" if evidence is weak
    
    The LLM is NEVER called without first passing through the evidence check.
    This is the primary defense against hallucinated medical information.
    
    For multimodal evidence:
    - Text/Document: Full content passed to LLM
    - Image: Reference only passed - LLM CANNOT interpret images
    
    ==========================================================================
    
    NOTE: This component does NOT perform retrieval.
    Evidence must be passed in from the retrieval layer.
    """

    async def reason(
        self,
        patient_id: str,
        query: str,
        evidence: list[dict],
        mode: str = "general",
    ) -> ReasoningResponse:
        """
        Generate evidence-grounded response.

        CRITICAL: Does NOT call LLM if evidence is empty.

        Args:
            patient_id: Patient identifier
            query: User question
            evidence: List of RetrievalEvidence dictionaries
            mode: "general" | "mental_health" | "summary"

        Returns:
            ReasoningResponse with answer and metadata
        """
        # =====================================================================
        # ANTI-HALLUCINATION GATE (CRITICAL)
        # =====================================================================
        # This check MUST remain at the top of this method.
        # NO LLM call is made if evidence is empty.
        # This applies to ALL modalities: text, document, image.
        # If retrieval returns nothing across ANY modality, we return
        # a fixed safe response WITHOUT invoking the LLM.
        # =====================================================================
        if not evidence:
            response = ReasoningResponse(
                answer_text="Insufficient data in patient records to answer this question. No relevant memories were found.",
                has_context=False,
                evidence_count=0,
                sources_used=[],
                disclaimer="No patient records matched this query.",
                query=query,
                patient_id=patient_id,
            )
            return response
        # =====================================================================
        # END ANTI-HALLUCINATION GATE - Evidence exists, proceeding to LLM
        # =====================================================================

        # Build prompt based on mode
        if mode == "mental_health":
            system_prompt, user_prompt = self._build_mental_health_prompt(query, evidence)
        elif mode == "summary":
            system_prompt, user_prompt = self._build_summary_prompt(evidence)
        else:
            system_prompt, user_prompt = self._build_qa_prompt(query, evidence)

        # Call LLM
        answer = await llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Low for factual accuracy
        )

        # Extract sources used
        sources = list(set(e.get("source", "unknown") for e in evidence))

        # Answer post-processing
        # If the LLM says "Insufficient data", we downgrade the evidence status
        # even if we technically found chunks.
        clean_answer = answer.strip()
        is_insufficient = (
            "Insufficient data" in clean_answer or 
            "do not contain relevant data" in clean_answer or
            "No patient records matched" in clean_answer
        )

        return ReasoningResponse(
            answer_text=clean_answer,
            has_context=not is_insufficient,
            evidence_count=0 if is_insufficient else len(evidence),
            sources_used=[] if is_insufficient else sources,
            disclaimer=SAFETY_DISCLAIMER.strip(),
            query=query,
            patient_id=patient_id,
        )

    def _build_qa_prompt(
        self,
        question: str,
        evidence: list[dict],
    ) -> tuple[str, str]:
        """Build general Q&A prompt."""
        evidence_text = format_evidence_for_prompt(evidence)
        user_prompt = EVIDENCE_QA_PROMPT.format(
            evidence=evidence_text,
            question=question,
        )
        return SYSTEM_PROMPT_HEALTHCARE, user_prompt

    def _build_mental_health_prompt(
        self,
        question: str,
        evidence: list[dict],
    ) -> tuple[str, str]:
        """Build mental health query prompt."""
        evidence_text = format_evidence_for_prompt(evidence)
        user_prompt = MENTAL_HEALTH_PROMPT.format(
            evidence=evidence_text,
            question=question,
        )
        return SYSTEM_PROMPT_MENTAL_HEALTH, user_prompt

    def _build_summary_prompt(
        self,
        evidence: list[dict],
    ) -> tuple[str, str]:
        """Build summarization prompt."""
        evidence_text = format_evidence_for_prompt(evidence)
        user_prompt = SUMMARIZE_EVIDENCE_PROMPT.format(evidence=evidence_text)
        return SYSTEM_PROMPT_HEALTHCARE, user_prompt

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    async def answer_question(
        self,
        patient_id: str,
        query: str,
        evidence: list[dict],
    ) -> ReasoningResponse:
        """Answer a general healthcare question."""
        return await self.reason(
            patient_id=patient_id,
            query=query,
            evidence=evidence,
            mode="general",
        )

    async def mental_health_response(
        self,
        patient_id: str,
        query: str,
        evidence: list[dict],
    ) -> ReasoningResponse:
        """Generate empathetic mental health response."""
        return await self.reason(
            patient_id=patient_id,
            query=query,
            evidence=evidence,
            mode="mental_health",
        )


    async def summarize_records(
        self,
        patient_id: str,
        evidence: list[dict],
    ) -> ReasoningResponse:
        """Summarize patient records."""
        return await self.reason(
            patient_id=patient_id,
            query="Summarize patient records",
            evidence=evidence,
            mode="summary",
        )

    async def suggest_followup_questions(
        self,
        evidence: list[dict],
    ) -> list[str]:
        """Generate smart follow-up questions based on evidence."""
        if not evidence:
            return ["What is the patient's primary complaint?", "Are there any known allergies?", "What current medications is the patient taking?"]
            
        system_prompt, user_prompt = self._build_suggestion_prompt(evidence)
        
        try:
            # We use generate_with_json here since we want a structured list
            return await llm_client.generate_with_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
        except Exception:
            # Fallback if JSON parsing fails
            return ["Review recent symptoms", "Check medication adherence", "Assess current mood"]

    def _build_suggestion_prompt(
        self,
        evidence: list[dict],
    ) -> tuple[str, str]:
        """Build suggestion prompt."""
        from app.reasoning.prompts import SUGGEST_QUESTIONS_PROMPT
        
        evidence_text = format_evidence_for_prompt(evidence)
        user_prompt = SUGGEST_QUESTIONS_PROMPT.format(evidence=evidence_text)
        return SYSTEM_PROMPT_HEALTHCARE, user_prompt



# Singleton instance
reasoning_chain = ReasoningChain()
