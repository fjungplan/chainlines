"""Tests for prompt-specific model routing."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

from app.scraper.llm.model_config import PromptType, MODEL_ROUTING
from app.scraper.llm.service import LLMService


class DummyResponse(BaseModel):
    """Dummy response model for testing."""
    value: str


class TestModelConfig:
    """Tests for model configuration."""
    
    def test_extract_team_data_uses_flash_primary(self):
        """EXTRACT_TEAM_DATA should use gemini-2.5-flash as primary."""
        config = MODEL_ROUTING[PromptType.EXTRACT_TEAM_DATA]
        assert config.primary_model == "gemini-2.5-flash"
        assert config.fallback_model == "deepseek-chat"
    
    def test_decide_lineage_uses_reasoner_primary(self):
        """DECIDE_LINEAGE should use deepseek-reasoner as primary."""
        config = MODEL_ROUTING[PromptType.DECIDE_LINEAGE]
        assert config.primary_model == "deepseek-reasoner"
        assert config.fallback_model == "gemini-2.5-pro"
    
    def test_sponsor_extraction_uses_chat_primary(self):
        """SPONSOR_EXTRACTION should use deepseek-chat as primary."""
        config = MODEL_ROUTING[PromptType.SPONSOR_EXTRACTION]
        assert config.primary_model == "deepseek-chat"
        assert config.fallback_model == "gemini-2.5-flash"


class TestLLMServiceRouting:
    """Tests for LLM service prompt-based routing."""
    
    @pytest.fixture
    def mock_gemini_flash(self):
        """Mock Gemini Flash client."""
        client = MagicMock()
        client.generate_structured = AsyncMock(
            return_value=DummyResponse(value="gemini-flash")
        )
        client.model_id = "gemini-2.5-flash"
        return client
    
    @pytest.fixture
    def mock_gemini_pro(self):
        """Mock Gemini Pro client."""
        client = MagicMock()
        client.generate_structured = AsyncMock(
            return_value=DummyResponse(value="gemini-pro")
        )
        client.model_id = "gemini-2.5-pro"
        return client
    
    @pytest.fixture
    def mock_deepseek_chat(self):
        """Mock Deepseek Chat client."""
        client = MagicMock()
        client.generate_structured = AsyncMock(
            return_value=DummyResponse(value="deepseek-chat")
        )
        client.model_id = "deepseek-chat"
        return client
    
    @pytest.fixture
    def mock_deepseek_reasoner(self):
        """Mock Deepseek Reasoner client."""
        client = MagicMock()
        client.generate_structured = AsyncMock(
            return_value=DummyResponse(value="deepseek-reasoner")
        )
        client.model_id = "deepseek-reasoner"
        return client
    
    @pytest.mark.asyncio
    async def test_extract_team_data_routes_to_gemini_flash(
        self, mock_gemini_flash, mock_deepseek_chat
    ):
        """EXTRACT_TEAM_DATA should route to gemini-2.5-flash."""
        service = LLMService(clients={
            "gemini-2.5-flash": mock_gemini_flash,
            "deepseek-chat": mock_deepseek_chat,
        })
        
        result = await service.generate_structured(
            prompt="test",
            response_model=DummyResponse,
            prompt_type=PromptType.EXTRACT_TEAM_DATA
        )
        
        assert result.value == "gemini-flash"
        mock_gemini_flash.generate_structured.assert_awaited_once()
        mock_deepseek_chat.generate_structured.assert_not_awaited()
    
    @pytest.mark.asyncio
    async def test_decide_lineage_routes_to_deepseek_reasoner(
        self, mock_deepseek_reasoner, mock_gemini_pro
    ):
        """DECIDE_LINEAGE should route to deepseek-reasoner."""
        service = LLMService(clients={
            "deepseek-reasoner": mock_deepseek_reasoner,
            "gemini-2.5-pro": mock_gemini_pro,
        })
        
        result = await service.generate_structured(
            prompt="test",
            response_model=DummyResponse,
            prompt_type=PromptType.DECIDE_LINEAGE
        )
        
        assert result.value == "deepseek-reasoner"
        mock_deepseek_reasoner.generate_structured.assert_awaited_once()
        mock_gemini_pro.generate_structured.assert_not_awaited()
    
    @pytest.mark.asyncio
    async def test_sponsor_extraction_routes_to_deepseek_chat(
        self, mock_deepseek_chat, mock_gemini_flash
    ):
        """SPONSOR_EXTRACTION should route to deepseek-chat."""
        service = LLMService(clients={
            "deepseek-chat": mock_deepseek_chat,
            "gemini-2.5-flash": mock_gemini_flash,
        })
        
        result = await service.generate_structured(
            prompt="test",
            response_model=DummyResponse,
            prompt_type=PromptType.SPONSOR_EXTRACTION
        )
        
        assert result.value == "deepseek-chat"
        mock_deepseek_chat.generate_structured.assert_awaited_once()
        mock_gemini_flash.generate_structured.assert_not_awaited()
    
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(
        self, mock_gemini_flash, mock_deepseek_chat
    ):
        """Should fallback to secondary model on primary failure."""
        mock_gemini_flash.generate_structured = AsyncMock(
            side_effect=Exception("Primary failed")
        )
        
        service = LLMService(clients={
            "gemini-2.5-flash": mock_gemini_flash,
            "deepseek-chat": mock_deepseek_chat,
        })
        
        result = await service.generate_structured(
            prompt="test",
            response_model=DummyResponse,
            prompt_type=PromptType.EXTRACT_TEAM_DATA
        )
        
        assert result.value == "deepseek-chat"
        mock_gemini_flash.generate_structured.assert_awaited_once()
        mock_deepseek_chat.generate_structured.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_raises_if_both_fail(
        self, mock_gemini_flash, mock_deepseek_chat
    ):
        """Should raise if both primary and fallback fail."""
        mock_gemini_flash.generate_structured = AsyncMock(
            side_effect=Exception("Primary failed")
        )
        mock_deepseek_chat.generate_structured = AsyncMock(
            side_effect=Exception("Fallback failed")
        )
        
        service = LLMService(clients={
            "gemini-2.5-flash": mock_gemini_flash,
            "deepseek-chat": mock_deepseek_chat,
        })
        
        with pytest.raises(Exception, match="Fallback failed"):
            await service.generate_structured(
                prompt="test",
                response_model=DummyResponse,
                prompt_type=PromptType.EXTRACT_TEAM_DATA
            )
