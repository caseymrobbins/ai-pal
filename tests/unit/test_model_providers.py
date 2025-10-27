"""
Unit Tests for Model Providers

Tests the three model providers:
- AnthropicProvider (Claude models)
- OpenAIProvider (GPT models)
- LocalProvider (Ollama/phi-2)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

from ai_pal.models.anthropic_provider import AnthropicProvider
from ai_pal.models.openai_provider import OpenAIProvider
from ai_pal.models.local import LocalProvider
from ai_pal.models.base import LLMRequest, LLMResponse


# ============================================================================
# Anthropic Provider Tests
# ============================================================================


@pytest.mark.asyncio
async def test_anthropic_provider_generate():
    """Test Anthropic provider basic generation"""
    provider = AnthropicProvider(api_key="test-key")

    # Mock the client
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response from Claude")]
    mock_response.usage = Mock(input_tokens=10, output_tokens=20)
    mock_response.stop_reason = "end_turn"

    with patch.object(provider, 'client') as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
        )

        response = await provider.generate(request)

        assert response.generated_text == "Test response from Claude"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30
        assert response.finish_reason == "end_turn"


@pytest.mark.asyncio
async def test_anthropic_provider_with_system_prompt():
    """Test Anthropic provider with system prompt"""
    provider = AnthropicProvider(api_key="test-key")

    mock_response = Mock()
    mock_response.content = [Mock(text="Response")]
    mock_response.usage = Mock(input_tokens=15, output_tokens=25)
    mock_response.stop_reason = "end_turn"

    with patch.object(provider, 'client') as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant.",
            max_tokens=100,
            temperature=0.7,
        )

        response = await provider.generate(request)

        # Verify system prompt was passed
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "system" in call_kwargs
        assert call_kwargs["system"] == "You are a helpful assistant."


@pytest.mark.asyncio
async def test_anthropic_cost_calculation():
    """Test Anthropic cost calculation for different models"""
    provider = AnthropicProvider(api_key="test-key")

    # Test Claude-3-opus (most expensive)
    cost_opus = provider._calculate_cost("claude-3-opus-20240229", 1000, 1000)
    assert cost_opus > 0

    # Test Claude-3-sonnet (mid-tier)
    cost_sonnet = provider._calculate_cost("claude-3-sonnet-20240229", 1000, 1000)
    assert cost_sonnet > 0
    assert cost_sonnet < cost_opus

    # Test Claude-3-haiku (cheapest)
    cost_haiku = provider._calculate_cost("claude-3-haiku-20240307", 1000, 1000)
    assert cost_haiku > 0
    assert cost_haiku < cost_sonnet


# ============================================================================
# OpenAI Provider Tests
# ============================================================================


@pytest.mark.asyncio
async def test_openai_provider_generate():
    """Test OpenAI provider basic generation"""
    provider = OpenAIProvider(api_key="test-key")

    # Mock the client
    mock_choice = Mock()
    mock_choice.message = Mock(content="Test response from GPT")
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    with patch.object(provider, 'client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
        )

        response = await provider.generate(request)

        assert response.generated_text == "Test response from GPT"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30
        assert response.finish_reason == "stop"


@pytest.mark.asyncio
async def test_openai_provider_with_system_prompt():
    """Test OpenAI provider with system prompt"""
    provider = OpenAIProvider(api_key="test-key")

    mock_choice = Mock()
    mock_choice.message = Mock(content="Response")
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock(prompt_tokens=15, completion_tokens=25, total_tokens=40)

    with patch.object(provider, 'client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant.",
            max_tokens=100,
            temperature=0.7,
        )

        response = await provider.generate(request)

        # Verify system prompt was included in messages
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "messages" in call_kwargs
        messages = call_kwargs["messages"]
        assert any(msg["role"] == "system" for msg in messages)


@pytest.mark.asyncio
async def test_openai_cost_calculation():
    """Test OpenAI cost calculation for different models"""
    provider = OpenAIProvider(api_key="test-key")

    # Test GPT-4 (expensive)
    cost_gpt4 = provider._calculate_cost("gpt-4", 1000, 1000)
    assert cost_gpt4 > 0

    # Test GPT-3.5-turbo (cheap)
    cost_gpt35 = provider._calculate_cost("gpt-3.5-turbo", 1000, 1000)
    assert cost_gpt35 > 0
    assert cost_gpt35 < cost_gpt4


# ============================================================================
# Local Provider Tests
# ============================================================================


@pytest.mark.asyncio
async def test_local_provider_generate():
    """Test Local provider basic generation"""
    provider = LocalProvider(base_url="http://localhost:11434")

    # Mock HTTP response
    mock_response = Mock()
    mock_response.json = Mock(return_value={
        "response": "Test response from local model",
        "done": True,
    })
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        request = LLMRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
        )

        response = await provider.generate(request)

        assert response.generated_text == "Test response from local model"
        assert response.cost_usd == 0.0  # Local models are free
        assert response.provider == "local"


@pytest.mark.asyncio
async def test_local_provider_with_system_prompt():
    """Test Local provider with system prompt"""
    provider = LocalProvider(base_url="http://localhost:11434")

    mock_response = Mock()
    mock_response.json = Mock(return_value={
        "response": "Response",
        "done": True,
    })
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        request = LLMRequest(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant.",
            max_tokens=100,
            temperature=0.7,
        )

        response = await provider.generate(request)

        # Verify system prompt was included
        call_kwargs = mock_post.call_args[1]
        assert "json" in call_kwargs
        assert "system" in call_kwargs["json"]


@pytest.mark.asyncio
async def test_local_provider_cost_always_zero():
    """Test that local provider always returns zero cost"""
    provider = LocalProvider(base_url="http://localhost:11434")

    mock_response = Mock()
    mock_response.json = Mock(return_value={
        "response": "Response",
        "done": True,
    })
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        request = LLMRequest(
            prompt="Test prompt" * 1000,  # Very long prompt
            max_tokens=1000,
        )

        response = await provider.generate(request)

        # Cost should always be zero for local
        assert response.cost_usd == 0.0


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_anthropic_provider_handles_api_error():
    """Test Anthropic provider handles API errors gracefully"""
    provider = AnthropicProvider(api_key="test-key")

    with patch.object(provider, 'client') as mock_client:
        mock_client.messages.create = AsyncMock(side_effect=Exception("API Error"))

        request = LLMRequest(prompt="Test", max_tokens=100)

        with pytest.raises(Exception) as exc_info:
            await provider.generate(request)

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_openai_provider_handles_api_error():
    """Test OpenAI provider handles API errors gracefully"""
    provider = OpenAIProvider(api_key="test-key")

    with patch.object(provider, 'client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        request = LLMRequest(prompt="Test", max_tokens=100)

        with pytest.raises(Exception) as exc_info:
            await provider.generate(request)

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_local_provider_handles_connection_error():
    """Test Local provider handles connection errors gracefully"""
    provider = LocalProvider(base_url="http://localhost:11434")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection refused")

        request = LLMRequest(prompt="Test", max_tokens=100)

        with pytest.raises(Exception) as exc_info:
            await provider.generate(request)

        assert "Connection refused" in str(exc_info.value)


# ============================================================================
# Token Counting Tests
# ============================================================================


@pytest.mark.asyncio
async def test_anthropic_token_counting():
    """Test Anthropic provider reports correct token counts"""
    provider = AnthropicProvider(api_key="test-key")

    mock_response = Mock()
    mock_response.content = [Mock(text="Response")]
    mock_response.usage = Mock(input_tokens=50, output_tokens=75)
    mock_response.stop_reason = "end_turn"

    with patch.object(provider, 'client') as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(prompt="Test", max_tokens=100)
        response = await provider.generate(request)

        assert response.prompt_tokens == 50
        assert response.completion_tokens == 75
        assert response.total_tokens == 125


@pytest.mark.asyncio
async def test_openai_token_counting():
    """Test OpenAI provider reports correct token counts"""
    provider = OpenAIProvider(api_key="test-key")

    mock_choice = Mock()
    mock_choice.message = Mock(content="Response")
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock(prompt_tokens=60, completion_tokens=80, total_tokens=140)

    with patch.object(provider, 'client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(prompt="Test", max_tokens=100)
        response = await provider.generate(request)

        assert response.prompt_tokens == 60
        assert response.completion_tokens == 80
        assert response.total_tokens == 140


# ============================================================================
# Model Selection Tests
# ============================================================================


@pytest.mark.asyncio
async def test_anthropic_model_selection():
    """Test Anthropic provider uses specified model"""
    provider = AnthropicProvider(api_key="test-key", model="claude-3-opus-20240229")

    mock_response = Mock()
    mock_response.content = [Mock(text="Response")]
    mock_response.usage = Mock(input_tokens=10, output_tokens=20)
    mock_response.stop_reason = "end_turn"

    with patch.object(provider, 'client') as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(prompt="Test", max_tokens=100)
        response = await provider.generate(request)

        # Verify correct model was used
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-3-opus-20240229"
        assert response.model_name == "claude-3-opus-20240229"


@pytest.mark.asyncio
async def test_openai_model_selection():
    """Test OpenAI provider uses specified model"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")

    mock_choice = Mock()
    mock_choice.message = Mock(content="Response")
    mock_choice.finish_reason = "stop"

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    with patch.object(provider, 'client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        request = LLMRequest(prompt="Test", max_tokens=100)
        response = await provider.generate(request)

        # Verify correct model was used
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert response.model_name == "gpt-4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
