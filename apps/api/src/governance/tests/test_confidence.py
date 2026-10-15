"""Unit and API integration tests for the review-priority and confidence engine."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from governance.confidence.engine import ReviewPriorityEngine
from governance.confidence.schemas import ConfidenceEvaluationRequest
from shared.db.models import Agent, AgentVersion, Approval, EvalRun, EvalSuite, Run

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_confidence_schema_validation_signal(db_session: AsyncSession) -> None:
    """Verify JSON Schema validation signal correctly handles conformant and invalid outputs."""
    engine = ReviewPriorityEngine()
    agent_id = str(uuid.uuid4())

    schema = {
        "type": "object",
        "required": ["company", "score"],
        "properties": {
            "company": {"type": "string"},
            "score": {"type": "number"},
        },
    }

    # Case 1: Valid dictionary matching schema
    req1 = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output={"company": "Acme Inc", "score": 9.5},
        schema_def=schema,
    )
    outcome1 = await engine.evaluate(db_session, req1)
    schema_signal1 = next(s for s in outcome1.signals if s.name == "schema_validation")
    assert schema_signal1.passed is True
    assert schema_signal1.score == 1.0

    # Case 2: Valid JSON string matching schema
    req2 = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output='{"company": "Acme Inc", "score": 9.5}',
        schema_def=schema,
    )
    outcome2 = await engine.evaluate(db_session, req2)
    schema_signal2 = next(s for s in outcome2.signals if s.name == "schema_validation")
    assert schema_signal2.passed is True
    assert schema_signal2.score == 1.0

    # Case 3: Invalid JSON string
    req3 = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output="not json {{{{",
        schema_def=schema,
    )
    outcome3 = await engine.evaluate(db_session, req3)
    schema_signal3 = next(s for s in outcome3.signals if s.name == "schema_validation")
    assert schema_signal3.passed is False
    assert schema_signal3.score == 0.0

    # Case 4: Non-conformant dictionary missing required field
    req4 = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output={"company": "Acme Inc"},
        schema_def=schema,
    )
    outcome4 = await engine.evaluate(db_session, req4)
    schema_signal4 = next(s for s in outcome4.signals if s.name == "schema_validation")
    assert schema_signal4.passed is False
    assert schema_signal4.score == 0.0

    # Case 5: No schema defined, non-empty output
    req5 = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output="Hello world from agent",
        schema_def=None,
    )
    outcome5 = await engine.evaluate(db_session, req5)
    schema_signal5 = next(s for s in outcome5.signals if s.name == "schema_validation")
    assert schema_signal5.passed is True
    assert schema_signal5.score == 1.0


@pytest.mark.asyncio
async def test_confidence_grounding_signal(db_session: AsyncSession) -> None:
    """Verify grounding and citation overlap signal against input context."""
    engine = ReviewPriorityEngine()
    agent_id = str(uuid.uuid4())

    source_context = (
        "Acme Corp announced record revenue of $100M for Q3 2026, driven by enterprise AI adoption."
    )

    # Case 1: High keyword overlap
    grounded_output = "Acme Corp reported record revenue with enterprise AI adoption in Q3 2026."
    req_high = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output=grounded_output,
        input_context=source_context,
    )
    res_high = await engine.evaluate(db_session, req_high)
    ground_signal_high = next(s for s in res_high.signals if s.name == "grounding_citation")
    assert ground_signal_high.passed is True
    assert ground_signal_high.score >= 0.8

    # Case 2: Low / ungrounded hallucination
    hallucinated_output = "Bananas and pineapples grow abundantly in tropical rainforest climates."
    req_low = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output=hallucinated_output,
        input_context=source_context,
    )
    res_low = await engine.evaluate(db_session, req_low)
    ground_signal_low = next(s for s in res_low.signals if s.name == "grounding_citation")
    assert ground_signal_low.passed is False
    assert ground_signal_low.score < 0.4

    # Case 3: No input context provided (neutral prior)
    req_none = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output="Generic response",
        input_context=None,
    )
    res_none = await engine.evaluate(db_session, req_none)
    ground_signal_none = next(s for s in res_none.signals if s.name == "grounding_citation")
    assert ground_signal_none.passed is True
    assert ground_signal_none.score == 1.0


@pytest.mark.asyncio
async def test_confidence_eval_benchmark_signal(db_session: AsyncSession) -> None:
    """Verify offline evaluation benchmark signal queries real completed runs."""
    engine = ReviewPriorityEngine()

    agent = Agent(name="eval-signal-agent", owner="engineer@example.com", stage="prototype")
    db_session.add(agent)
    await db_session.flush()

    ver = AgentVersion(
        agent_id=agent.id,
        version="1.0.0",
        spec={"metadata": {"name": agent.name, "owner": "engineer@example.com"}},
    )
    db_session.add(ver)
    await db_session.flush()

    suite = EvalSuite(
        name="Benchmark Suite",
        agent_id=agent.id,
        description="Core sanity check",
        config={"assertions": []},
    )
    db_session.add(suite)
    await db_session.flush()

    # Case 1: No completed runs yet
    req1 = ConfidenceEvaluationRequest(
        agent_id=str(agent.id),
        version_id=str(ver.id),
        output="Some output",
    )
    res1 = await engine.evaluate(db_session, req1)
    eval_signal1 = next(s for s in res1.signals if s.name == "eval_benchmark")
    assert eval_signal1.passed is False
    assert eval_signal1.score == 0.5

    # Case 2: Completed run with 0.95 pass rate
    run = EvalRun(
        suite_id=suite.id,
        agent_id=agent.id,
        agent_version_id=ver.id,
        status="completed",
        trigger="manual",
        total_cases=10,
        passed_cases=9,
        failed_cases=1,
        pass_rate=0.90,
    )
    db_session.add(run)
    await db_session.commit()

    res2 = await engine.evaluate(db_session, req1)
    eval_signal2 = next(s for s in res2.signals if s.name == "eval_benchmark")
    assert eval_signal2.passed is True
    assert eval_signal2.score == 0.90


@pytest.mark.asyncio
async def test_confidence_approval_history_signal(db_session: AsyncSession) -> None:
    """Verify historical human operator approval rate signal calculation."""
    engine = ReviewPriorityEngine()

    agent = Agent(name="approval-signal-agent", owner="engineer@example.com", stage="staging")
    db_session.add(agent)
    await db_session.flush()

    # Case 1: No approval history -> neutral prior (0.7)
    req = ConfidenceEvaluationRequest(
        agent_id=str(agent.id),
        output="Testing approval history",
    )
    res1 = await engine.evaluate(db_session, req)
    app_signal1 = next(s for s in res1.signals if s.name == "approval_history")
    assert app_signal1.score == 0.7
    assert app_signal1.passed is True

    # Case 2: Record 4 approvals and 1 rejection (80% approved)
    run = Run(agent_id=agent.id, status="completed", trigger_type="manual")
    db_session.add(run)
    await db_session.flush()

    for _ in range(4):
        db_session.add(
            Approval(
                run_id=run.id,
                agent_id=agent.id,
                action_type="send_email",
                status="approved",
                proposed_payload={"to": "test@example.com"},
            )
        )
    db_session.add(
        Approval(
            run_id=run.id,
            agent_id=agent.id,
            action_type="send_email",
            status="rejected",
            proposed_payload={"to": "spam@example.com"},
        )
    )
    await db_session.commit()

    res2 = await engine.evaluate(db_session, req)
    app_signal2 = next(s for s in res2.signals if s.name == "approval_history")
    assert app_signal2.score == 0.8
    assert app_signal2.passed is True


@pytest.mark.asyncio
async def test_review_priority_classification(db_session: AsyncSession) -> None:
    """Verify review_priority bands: low, medium, high, critical."""
    engine = ReviewPriorityEngine()
    agent_id = str(uuid.uuid4())

    # Critical failure: schema violation and low grounding
    schema = {"type": "object", "required": ["strict_key"]}
    req_critical = ConfidenceEvaluationRequest(
        agent_id=agent_id,
        output="not conforming to schema",
        input_context="Totally unrelated source about apples and oranges",
        schema_def=schema,
    )
    out_critical = await engine.evaluate(db_session, req_critical)
    assert out_critical.review_priority in ("high", "critical")
    assert out_critical.confidence_score < 0.6


@pytest.mark.asyncio
async def test_confidence_api_endpoint(async_client: AsyncClient) -> None:
    """Test POST /api/v1/governance/confidence/evaluate endpoint."""
    agent_id = str(uuid.uuid4())
    payload = {
        "agent_id": agent_id,
        "output": {"summary": "Weekly pipeline report", "count": 42},
        "input_context": "Weekly pipeline report generated with count 42",
        "schema_def": {
            "type": "object",
            "required": ["summary", "count"],
            "properties": {
                "summary": {"type": "string"},
                "count": {"type": "integer"},
            },
        },
    }

    resp = await async_client.post("/api/v1/governance/confidence/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "confidence_score" in data
    assert "review_priority" in data
    assert data["review_priority"] in ("low", "medium", "high", "critical")
    assert len(data["signals"]) == 4
    signal_names = {s["name"] for s in data["signals"]}
    assert signal_names == {
        "schema_validation",
        "grounding_citation",
        "eval_benchmark",
        "approval_history",
    }
