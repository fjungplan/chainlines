"""Deepseek LLM client implementation (OpenAI-compatible API)."""
from typing import Type, TypeVar
from openai import AsyncOpenAI
import instructor
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class DeepseekClient:
    """Client for Deepseek API (OpenAI-compatible) with structured output."""
    
    def __init__(self, api_key: str, model: str = "deepseek-reasoner"):
        self._openai = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self._client = instructor.from_openai(
            self._openai,
            mode=instructor.Mode.JSON
        )
        self._model = model
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.1
    ) -> T:
        """Generate structured response."""
        return await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_model=response_model,
            temperature=temperature
        )
