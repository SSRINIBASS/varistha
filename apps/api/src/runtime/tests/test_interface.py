"""Unit tests for the Runtime protocol and MockRuntime adapter."""

from __future__ import annotations

import uuid

import pytest
from runtime.interface import RunContext, RunResult, Runtime
from runtime.mock import MockRuntime


def test_runtime_protocol_conformance() -> None:
    """MockRuntime satisfies the Runtime protocol."""
    mock = MockRuntime()
    assert isinstance(mock, Runtime)


@pytest.mark.asyncio
async def test_mock_runtime_successful_execution() -> None:
    """MockRuntime returns completed status with expected output and metrics."""
    runtime = MockRuntime(
        default_output={"summary": "All leads processed"},
        tokens=200,
        cost_usd=0.005,
    )

    context = RunContext(
        run_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        agent_name="lead-researcher",
        model="gpt-4o",
        instructions="Find tech founders in London.",
        input_data={"limit": 5},
    )

    result = await runtime.execute(context)

    assert isinstance(result, RunResult)
    assert result.status == "completed"
    assert result.output == {"summary": "All leads processed"}
    assert result.total_tokens == 200
    assert result.cost_usd == 0.005
    assert result.error is None
    assert len(runtime.executed_contexts) == 1
    assert runtime.executed_contexts[0].agent_name == "lead-researcher"


@pytest.mark.asyncio
async def test_mock_runtime_simulated_failure() -> None:
    """MockRuntime properly reports failure when configured."""
    runtime = MockRuntime(
        should_fail=True,
        error_message="Simulated LLM rate limit",
    )

    context = RunContext(
        run_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        agent_name="failing-agent",
        model="claude-3-5-sonnet",
        instructions="Some instructions",
    )

    result = await runtime.execute(context)

    assert result.status == "failed"
    assert result.output == {}
    assert result.error == "Simulated LLM rate limit"


@pytest.mark.asyncio
async def test_mock_runtime_waiting_approval() -> None:
    """MockRuntime sets status to waiting_approval for L1 outbound tasks."""
    runtime = MockRuntime(
        waiting_approval=True,
        default_output={"draft_email": "Hello, saw your launch!"},
    )

    context = RunContext(
        run_id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        agent_name="outbound-agent",
        model="gpt-4o",
        instructions="Draft email",
    )

    result = await runtime.execute(context)

    assert result.status == "waiting_approval"
    assert result.output == {"draft_email": "Hello, saw your launch!"}
    assert result.error is None
