"""Unit and integration tests for Eval Execution Engine and Evaluators Library."""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from governance.evals.engine import EvalExecutionEngine
from governance.evals.evaluators import create_evaluator
from governance.evals.evaluators.builtin import (
    ContainsEvaluator,
    ExactMatchEvaluator,
    GroundingEvaluator,
    JsonSchemaEvaluator,
    LLMRubricEvaluator,
    RegexEvaluator,
)
from shared.db.models.agent import Agent, AgentVersion

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def sample_agent_for_evals(db_session: AsyncSession) -> tuple[Agent, AgentVersion]:
    agent = Agent(
        name="eval-target-agent",
        owner="tester@varistha.io",
        stage="dev",
    )
    db_session.add(agent)
    await db_session.flush()

    version = AgentVersion(
        agent_id=agent.id,
        version="1.0.0",
        spec={
            "apiVersion": "varistha/v1",
            "kind": "Agent",
            "metadata": {"name": "eval-target-agent", "version": "1.0.0"},
            "spec": {
                "instructions": "Extract entities and return valid JSON.",
                "model": {"primary": "gpt-4o-mini"},
            },
        },
    )
    db_session.add(version)
    await db_session.flush()
    return agent, version


# -----------------------------------------------------------------------------
# Evaluator Unit Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exact_match_evaluator() -> None:
    evaluator = ExactMatchEvaluator()

    # Match
    res1 = await evaluator.evaluate("hello world", "hello world")
    assert res1.passed is True
    assert res1.score == 1.0
    assert res1.failure_reason is None

    # Strip match
    res2 = await evaluator.evaluate(" hello ", "hello")
    assert res2.passed is True

    # Mismatch
    res3 = await evaluator.evaluate("foo", "bar")
    assert res3.passed is False
    assert res3.score == 0.0
    assert "Expected 'bar' but received 'foo'" in str(res3.failure_reason)

    # Object match
    res4 = await evaluator.evaluate({"a": 1}, {"a": 1})
    assert res4.passed is True


@pytest.mark.asyncio
async def test_contains_evaluator() -> None:
    evaluator = ContainsEvaluator()

    # Substring in string
    res1 = await evaluator.evaluate("The quick brown fox jumps", "brown fox")
    assert res1.passed is True
    assert res1.score == 1.0

    # Key-value in dict
    res2 = await evaluator.evaluate({"status": "ok", "code": 200}, {"status": "ok"})
    assert res2.passed is True

    # Item in list
    res3 = await evaluator.evaluate(["alpha", "beta", "gamma"], "beta")
    assert res3.passed is True

    # Not found
    res4 = await evaluator.evaluate("The quick brown fox", "elephant")
    assert res4.passed is False
    assert "Output did not contain expected content" in str(res4.failure_reason)


@pytest.mark.asyncio
async def test_regex_evaluator() -> None:
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    evaluator = RegexEvaluator(config={"pattern": email_pattern})

    # Valid email
    res1 = await evaluator.evaluate("Contact us at support@example.com immediately.")
    assert res1.passed is True
    assert res1.score == 1.0

    # Invalid email
    res2 = await evaluator.evaluate("Contact us at support dot example dot com.")
    assert res2.passed is False
    assert res2.score == 0.0
    assert "Output did not match regex pattern" in str(res2.failure_reason)

    # Broken regex pattern
    broken_eval = RegexEvaluator(config={"pattern": r"[unclosed-bracket"})
    res3 = await broken_eval.evaluate("test text")
    assert res3.passed is False
    assert "Invalid regex pattern" in str(res3.failure_reason)


@pytest.mark.asyncio
async def test_json_schema_evaluator() -> None:
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "score": {"type": "number"},
        },
        "required": ["name", "score"],
    }
    evaluator = JsonSchemaEvaluator(config={"schema": schema})

    # Valid dict
    res1 = await evaluator.evaluate({"name": "Agent 1", "score": 98.5})
    assert res1.passed is True

    # Valid JSON string
    res2 = await evaluator.evaluate('{"name": "Agent 2", "score": 85}')
    assert res2.passed is True

    # Schema violation (missing required key)
    res3 = await evaluator.evaluate({"name": "Agent 3"})
    assert res3.passed is False
    assert "JSON Schema validation error" in str(res3.failure_reason)

    # Invalid JSON string
    res4 = await evaluator.evaluate("not a json string at all")
    assert res4.passed is False
    assert "Output is not valid JSON string" in str(res4.failure_reason)

    # Missing schema config
    empty_schema_eval = JsonSchemaEvaluator()
    res5 = await empty_schema_eval.evaluate({"name": "Agent 1"})
    assert res5.passed is False
    assert "No valid JSON Schema definition provided" in str(res5.failure_reason)


@pytest.mark.asyncio
async def test_grounding_evaluator() -> None:
    evaluator = GroundingEvaluator(threshold=0.4)

    context = {"input": "Varistha provides autonomy levels L0 to L4 for startup employee agents."}

    # High grounding overlap
    res1 = await evaluator.evaluate(
        "Startup employee agents have autonomy levels from L0 to L4.",
        context=context,
    )
    assert res1.passed is True
    assert res1.score >= 0.4

    # Completely fabricated output with low overlap
    res2 = await evaluator.evaluate(
        "Chocolate ice cream tastes wonderfully delicious with strawberry syrup.",
        context=context,
    )
    assert res2.passed is False
    assert res2.score < 0.4
    assert "Grounding ratio" in str(res2.failure_reason)

    # Empty output
    res3 = await evaluator.evaluate("", context=context)
    assert res3.passed is True


@pytest.mark.asyncio
async def test_llm_rubric_evaluator() -> None:
    evaluator = LLMRubricEvaluator(threshold=0.8)

    # Mock LiteLLM acompletion
    mock_resp = MagicMock()
    mock_payload = {"score": 0.95, "reasoning": "Excellent detailed answer."}
    mock_resp.choices = [MagicMock(message=MagicMock(content=json.dumps(mock_payload)))]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
        mock_litellm.return_value = mock_resp
        res = await evaluator.evaluate("actual output", expected="expected ground truth")
        assert res.passed is True
        assert res.score == 0.95
        assert res.metadata.get("reasoning") == "Excellent detailed answer."

    # Mock failure score
    mock_fail_resp = MagicMock()
    mock_fail_payload = {"score": 0.4, "reasoning": "Missed key details."}
    mock_fail_resp.choices = [MagicMock(message=MagicMock(content=json.dumps(mock_fail_payload)))]
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
        mock_litellm.return_value = mock_fail_resp
        res2 = await evaluator.evaluate("bad output")
        assert res2.passed is False
        assert res2.score == 0.4
        assert "LLM judge scored 0.40" in str(res2.failure_reason)

    # Mock network / API error
    with patch("litellm.acompletion", side_effect=RuntimeError("LiteLLM connection timeout")):
        res3 = await evaluator.evaluate("output")
        assert res3.passed is False
        assert res3.score == 0.0
        assert "LLM rubric evaluator error" in str(res3.failure_reason)


def test_evaluator_factory() -> None:
    ev1 = create_evaluator({"type": "exact-match", "name": "strict-match"})
    assert isinstance(ev1, ExactMatchEvaluator)
    assert ev1.name == "strict-match"

    ev2 = create_evaluator({"type": "contains"})
    assert isinstance(ev2, ContainsEvaluator)

    ev3 = create_evaluator({"type": "regex", "config": {"pattern": r"\d+"}})
    assert isinstance(ev3, RegexEvaluator)

    ev4 = create_evaluator({"type": "json-schema"})
    assert isinstance(ev4, JsonSchemaEvaluator)

    ev5 = create_evaluator({"type": "grounding"})
    assert isinstance(ev5, GroundingEvaluator)

    ev6 = create_evaluator({"type": "llm-rubric"})
    assert isinstance(ev6, LLMRubricEvaluator)

    # Unknown fallback raises ValueError
    with pytest.raises(ValueError, match="Unknown evaluator type"):
        create_evaluator({"type": "unsupported-custom-type"})


# -----------------------------------------------------------------------------
# Engine Execution Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_engine_execute_suite_with_custom_runner(
    db_session: AsyncSession,
    sample_agent_for_evals: tuple[Agent, AgentVersion],
) -> None:
    agent, version = sample_agent_for_evals
    engine = EvalExecutionEngine()

    from governance.evals import service
    from governance.evals.schemas import EvalSuiteCreate

    suite = await service.create_or_update_eval_suite(
        db_session,
        EvalSuiteCreate(
            agent_id=agent.id,
            name="customer-sentiment-suite",
            description="Evaluates customer sentiment output.",
            config={
                "evaluators": [
                    {"name": "match-sentiment", "type": "exact-match"},
                    {"name": "contains-reason", "type": "contains", "threshold": 1.0},
                ],
                "cases": [
                    {
                        "id": "c1",
                        "name": "Positive Case",
                        "input": {"text": "I love Varistha, it saved 10 hours!"},
                        "expected": "positive",
                        "evaluators": ["match-sentiment"],
                    },
                    {
                        "id": "c2",
                        "name": "Negative Case",
                        "input": {"text": "System was down for an hour."},
                        "expected": "negative",
                        "evaluators": ["match-sentiment"],
                    },
                ],
            },
        ),
    )

    # Mock custom runner that returns expected outputs
    async def mock_runner(inp: dict[str, Any]) -> Any:
        if "love" in inp.get("text", ""):
            return "positive"
        return "negative"

    run = await engine.execute_suite(
        db=db_session,
        suite_id=suite.id,
        agent_version_id=version.id,
        runner=mock_runner,
        trigger="test-harness",
    )

    assert run.status == "completed"
    assert run.total_cases == 2
    assert run.passed_cases == 2
    assert run.pass_rate == 1.0
    assert run.duration_ms is not None
    assert run.duration_ms >= 0

    # Verify granular results
    run_detail = await service.get_eval_run(db_session, run.id)
    assert run_detail is not None
    assert len(run_detail.results) == 2
    assert run_detail.results[0].passed is True
    assert run_detail.results[0].case_name == "Positive Case"
    assert run_detail.results[1].passed is True


@pytest.mark.asyncio
async def test_engine_execute_empty_suite(
    db_session: AsyncSession,
    sample_agent_for_evals: tuple[Agent, AgentVersion],
) -> None:
    agent, version = sample_agent_for_evals
    engine = EvalExecutionEngine()

    from governance.evals import service
    from governance.evals.schemas import EvalSuiteCreate

    suite = await service.create_or_update_eval_suite(
        db_session,
        EvalSuiteCreate(
            agent_id=agent.id,
            name="empty-suite",
            config={"cases": []},
        ),
    )

    run = await engine.execute_suite(
        db=db_session,
        suite_id=suite.id,
        agent_version_id=version.id,
    )

    assert run.status == "completed"
    assert run.total_cases == 0
    assert run.passed_cases == 0
    assert run.pass_rate == 0.0


@pytest.mark.asyncio
async def test_engine_nonexistent_suite_raises_value_error(
    db_session: AsyncSession,
) -> None:
    engine = EvalExecutionEngine()
    with pytest.raises(ValueError, match="not found"):
        await engine.execute_suite(db=db_session, suite_id=uuid.uuid4())


# -----------------------------------------------------------------------------
# REST API Endpoint Test
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_execute_eval_suite(
    async_client: AsyncClient,
    sample_agent_for_evals: tuple[Agent, AgentVersion],
) -> None:
    agent, version = sample_agent_for_evals

    # 1. Create suite
    create_resp = await async_client.post(
        "/api/v1/evals/suites",
        json={
            "agent_id": str(agent.id),
            "name": "api-test-suite",
            "description": "API suite execution test.",
            "config": {
                "evaluators": [{"name": "exact", "type": "exact-match"}],
                "cases": [
                    {
                        "id": "c1",
                        "name": "Case 1",
                        "input": {"prompt": "ping"},
                        "expected": "pong",
                    }
                ],
            },
        },
    )
    assert create_resp.status_code == 201
    suite_id = create_resp.json()["id"]

    # Mock LiteLLM for execution
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="pong"))]
    mock_resp.usage = MagicMock(total_tokens=42)

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_litellm:
        mock_litellm.return_value = mock_resp

        exec_resp = await async_client.post(
            f"/api/v1/evals/suites/{suite_id}/execute?agent_version_id={version.id}&trigger=api-test"
        )
        assert exec_resp.status_code == 200
        run_data = exec_resp.json()
        assert run_data["status"] == "completed"
        assert run_data["total_cases"] == 1
        assert run_data["passed_cases"] == 1
        assert run_data["pass_rate"] == 1.0
        assert len(run_data["results"]) == 1
        assert run_data["results"][0]["passed"] is True
        assert run_data["results"][0]["actual_output"] == "pong"
