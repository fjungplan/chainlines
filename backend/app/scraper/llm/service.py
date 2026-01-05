"""LLM Service with fallback chain."""
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from app.scraper.llm.base import BaseLLMClient

T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger(__name__)

class LLMService:
    """LLM service with automatic fallback."""
    
    def __init__(
        self,
        primary: BaseLLMClient,
        secondary: Optional[BaseLLMClient] = None
    ):
        self._primary = primary
        self._secondary = secondary
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.1
    ) -> T:
        """Generate structured response with fallback on failure."""
        try:
            return await self._primary.generate_structured(
                prompt=prompt,
                response_model=response_model,
                temperature=temperature
            )
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}")
            if self._secondary:
                logger.info("Falling back to secondary LLM")
                return await self._secondary.generate_structured(
                    prompt=prompt,
                    response_model=response_model,
                    temperature=temperature
                )
            raise
