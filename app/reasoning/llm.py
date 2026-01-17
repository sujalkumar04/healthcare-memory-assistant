"""
LLM Client Abstraction (Component 6)

Wrapper for OpenAI-compatible LLM APIs.
"""

import os
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.core.exceptions import LLMError


class LLMClient:
    """
    LLM client wrapper for text generation.
    
    Supports:
    - OpenAI API
    - Azure OpenAI
    - Any OpenAI-compatible API (via base_url)
    """

    _instance: "LLMClient | None" = None
    _client: OpenAI | None = None

    def __new__(cls) -> "LLMClient":
        """Singleton pattern for client reuse."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> OpenAI:
        """Lazy-load the OpenAI-compatible Groq client."""
        if LLMClient._client is None:
            api_key = settings.GROQ_API_KEY
            if not api_key:
                # Fallback check for env var directly if not in settings object yet
                api_key = os.getenv("GROQ_API_KEY")
            
            if not api_key:
                raise LLMError("GROQ_API_KEY not configured")
            
            # Groq uses OpenAI-compatible API
            LLMClient._client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=30.0,
            )
        return LLMClient._client

    @property
    def model(self) -> str:
        """Get configured model name."""
        return settings.GROQ_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,  # Low temperature for factual responses
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Max tokens to generate
            temperature: Sampling temperature (lower = more deterministic)

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            raise LLMError(f"LLM generation failed: {e}")

    async def generate_with_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate and parse JSON response.
        
        Useful for structured outputs.
        """
        import json
        
        full_system = (system_prompt or "") + "\nRespond ONLY with valid JSON."
        
        text = await self.generate(
            prompt=prompt,
            system_prompt=full_system,
            temperature=0.1,  # Very low for structured output
        )
        
        # Extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse JSON response: {e}")


# Singleton instance
llm_client = LLMClient()
