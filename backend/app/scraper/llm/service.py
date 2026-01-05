"""LLM Service with prompt-specific model routing."""
import logging
from typing import Type, TypeVar, Optional, Dict

from pydantic import BaseModel

from app.scraper.llm.base import BaseLLMClient
from app.scraper.llm.model_config import PromptType, MODEL_ROUTING

T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger(__name__)


class LLMService:
    """LLM service with prompt-specific model routing and fallback.
    
    Each prompt type is routed to its designated primary/fallback model pair
    for cost optimization.
    """
    
    def __init__(
        self,
        clients: Optional[Dict[str, BaseLLMClient]] = None,
        # Legacy constructor support for backward compatibility
        primary: Optional[BaseLLMClient] = None,
        secondary: Optional[BaseLLMClient] = None
    ):
        """Initialize with a dictionary of LLM clients keyed by model ID.
        
        Args:
            clients: Dictionary mapping model IDs to their client instances.
            primary: (Deprecated) Legacy primary client for backward compatibility.
            secondary: (Deprecated) Legacy secondary client for backward compatibility.
        """
        if clients:
            self._clients = clients
            self._legacy_mode = False
        else:
            # Legacy mode: use old primary/secondary pattern
            self._primary = primary
            self._secondary = secondary
            self._legacy_mode = True
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.1,
        prompt_type: Optional[PromptType] = None
    ) -> T:
        """Generate structured response with prompt-specific model routing.
        
        Args:
            prompt: The prompt text to send to the LLM.
            response_model: Pydantic model class for structured output.
            temperature: Sampling temperature (default: 0.1).
            prompt_type: The type of prompt for model routing.
            
        Returns:
            Structured response matching the response_model.
            
        Raises:
            Exception: If both primary and fallback models fail.
        """
        if self._legacy_mode:
            return await self._generate_legacy(prompt, response_model, temperature)
        
        if prompt_type is None:
            raise ValueError("prompt_type is required for model routing")
        
        config = MODEL_ROUTING[prompt_type]
        primary_client = self._clients.get(config.primary_model)
        fallback_client = self._clients.get(config.fallback_model)
        
        if not primary_client:
            raise ValueError(f"No client registered for primary model: {config.primary_model}")
        
        try:
            logger.debug(f"Routing {prompt_type.value} to primary: {config.primary_model}")
            return await primary_client.generate_structured(
                prompt=prompt,
                response_model=response_model,
                temperature=temperature
            )
        except Exception as e:
            logger.warning(f"Primary model {config.primary_model} failed: {e}")
            
            if fallback_client:
                logger.info(f"Falling back to: {config.fallback_model}")
                return await fallback_client.generate_structured(
                    prompt=prompt,
                    response_model=response_model,
                    temperature=temperature
                )
            raise
    
    async def _generate_legacy(
        self,
        prompt: str,
        response_model: Type[T],
        temperature: float
    ) -> T:
        """Legacy generation using old primary/secondary pattern."""
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
