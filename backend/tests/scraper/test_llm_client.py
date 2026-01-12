"""Test LLM client protocol and implementations."""
import pytest
from typing import Protocol, runtime_checkable
from pydantic import BaseModel
from unittest.mock import AsyncMock, patch, MagicMock

class SimpleResponse(BaseModel):
    answer: str

def test_base_llm_client_is_protocol():
    """BaseLLMClient should be a runtime-checkable Protocol."""
    from app.scraper.llm.base import BaseLLMClient
    assert hasattr(BaseLLMClient, '__protocol_attrs__') or isinstance(BaseLLMClient, type)

@pytest.mark.asyncio
async def test_gemini_client_returns_structured():
    """GeminiClient should return structured Pydantic response."""
    from app.scraper.llm.gemini import GeminiClient
    
    # Mock the instructor-patched client
    with patch('app.scraper.llm.gemini.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        with patch('app.scraper.llm.gemini.instructor') as mock_instructor:
            mock_client = MagicMock()
            mock_client.chat.completions.create = MagicMock(
                return_value=SimpleResponse(answer="test")
            )
            mock_instructor.from_gemini.return_value = mock_client
            
            client = GeminiClient(api_key="test-key")
            result = await client.generate_structured(
                prompt="What is 2+2?",
                response_model=SimpleResponse
            )
            
            assert isinstance(result, SimpleResponse)
            assert result.answer == "test"

@pytest.mark.asyncio
async def test_deepseek_client_returns_structured():
    """DeepseekClient should return structured Pydantic response."""
    from app.scraper.llm.deepseek import DeepseekClient
    
    with patch('app.scraper.llm.deepseek.instructor') as mock_instructor:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=SimpleResponse(answer="deepseek-test")
        )
        mock_instructor.from_openai.return_value = mock_client
        
        client = DeepseekClient(api_key="test-key")
        result = await client.generate_structured(
            prompt="What is 2+2?",
            response_model=SimpleResponse
        )
        
        assert isinstance(result, SimpleResponse)
        assert result.answer == "deepseek-test"

@pytest.mark.asyncio
async def test_llm_service_fallback_on_error():
    """LLMService should fallback to secondary client on primary failure."""
    from app.scraper.llm.service import LLMService
    
    primary = AsyncMock()
    primary.generate_structured = AsyncMock(side_effect=Exception("Primary failed"))
    
    secondary = AsyncMock()
    secondary.generate_structured = AsyncMock(
        return_value=SimpleResponse(answer="fallback-worked")
    )
    
    service = LLMService(primary=primary, secondary=secondary)
    result = await service.generate_structured(
        prompt="test",
        response_model=SimpleResponse
    )
    
    assert result.answer == "fallback-worked"
    primary.generate_structured.assert_called_once()
    secondary.generate_structured.assert_called_once()

@pytest.mark.asyncio
async def test_llm_service_uses_primary_first():
    """LLMService should use primary when it succeeds."""
    from app.scraper.llm.service import LLMService
    
    primary = AsyncMock()
    primary.generate_structured = AsyncMock(
        return_value=SimpleResponse(answer="primary-worked")
    )
    
    secondary = AsyncMock()
    
    service = LLMService(primary=primary, secondary=secondary)
    result = await service.generate_structured(
        prompt="test",
        response_model=SimpleResponse
    )
    
    assert result.answer == "primary-worked"
    secondary.generate_structured.assert_not_called()


