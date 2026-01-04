"""Base LLM client protocol."""
from typing import Protocol, TypeVar, Type
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseLLMClient(Protocol):
    """Protocol for LLM clients."""
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.1
    ) -> T:
        """Generate a structured response matching the Pydantic model."""
        ...
