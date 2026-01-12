"""Gemini LLM client implementation."""
from typing import Type, TypeVar
import google.generativeai as genai
import instructor
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class GeminiClient:
    """Client for Google Gemini API with structured output."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self._client = instructor.from_gemini(
            client=self._model,
            mode=instructor.Mode.GEMINI_JSON
        )
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.1
    ) -> T:
        """Generate structured response."""
        # Note: instructor.from_gemini creates a sync client, so we don't await the create call
        # but we keep the method async for interface compatibility.
        return self._client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=response_model,
            generation_config={"temperature": temperature}
        )
