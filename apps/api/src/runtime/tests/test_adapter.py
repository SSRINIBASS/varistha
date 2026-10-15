"""Unit tests for the LangGraph runtime adapter with mocked LiteLLM."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from runtime.adapter import LangGraphRuntime
from runtime.interface import RunContext


@pytest.mark.asyncio
async def test_langgraph_adapter_success_json_response() -> None:
    """LangGraphRuntime parses JSON response content into structured dictionary."""
    adapter = LangGraphRuntime()

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"qualification": "Tier 1", "score": 95}'
    mock_response.choices = [mock_choice]
    mock_response.usage.total_tokens = 320

    with (
        patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
        patch("litellm.completion_cost", return_value=0.008) as mock_cost,
    ):
        mock_acompletion.return_value = mock_response

        context = RunContext(
            run_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            agent_name="lead-qualifier",
            model="gpt-4o",
            instructions="Score incoming lead.",
            input_data={"company": "Acme Corp", "employees": 200},
        )

        result = await adapter.execute(context)

        assert result.status == "completed"
        assert result.output == {"qualification": "Tier 1", "score": 95}
        assert result.total_tokens == 320
        assert result.cost_usd == 0.008
        assert result.error is None
        mock_acompletion.assert_awaited_once()
        mock_cost.assert_called_once()


@pytest.mark.asyncio
async def test_langgraph_adapter_success_text_response() -> None:
    """LangGraphRuntime wraps non-JSON text in a response field."""
    adapter = LangGraphRuntime()

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a plain text summary response."
    mock_response.choices = [mock_choice]
    mock_response.usage.total_tokens = 45

    with (
        patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion,
        patch("litellm.completion_cost", return_value=0.001),
    ):
        mock_acompletion.return_value = mock_response

        context = RunContext(
            run_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            agent_name="summarizer",
            model="gpt-4o",
            instructions="Summarize text.",
            input_data={"prompt": "Summarize this article."},
        )

        result = await adapter.execute(context)

        assert result.status == "completed"
        assert result.output == {"response": "This is a plain text summary response."}
        assert result.total_tokens == 45


@pytest.mark.asyncio
async def test_langgraph_adapter_handles_litellm_exception() -> None:
    """LangGraphRuntime captures LiteLLM API errors and returns failed status."""
    adapter = LangGraphRuntime()

    with patch(
        "litellm.acompletion",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LiteLLM connection timed out"),
    ):
        context = RunContext(
            run_id=uuid.uuid4(),
            agent_id=uuid.uuid4(),
            agent_name="timeout-agent",
            model="gpt-4o",
            instructions="Do something",
        )

        result = await adapter.execute(context)

        assert result.status == "failed"
        assert result.output == {}
        assert "timed out" in (result.error or "")
