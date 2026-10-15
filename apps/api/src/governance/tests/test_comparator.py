"""Unit and API integration tests for evaluation run version regression comparator."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from governance.evals.comparator import compare_eval_runs
from shared.db.models import Agent, AgentVersion, EvalResult, EvalRun, EvalSuite

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


def _make_eval_run(
    suite_id: uuid.UUID,
    agent_id: uuid.UUID,
    agent_version_id: uuid.UUID | None,
    results_data: list[tuple[str, str, bool, float]],
    duration_ms: int = 1200,
) -> EvalRun:
    """Construct an EvalRun with EvalResult records for testing."""
    run_id = uuid.uuid4()
    results = [
        EvalResult(
            eval_run_id=run_id,
            case_id=cid,
            case_name=cname,
            passed=passed,
            score=score,
            evaluator_name="default",
            evaluator_type="exact_match",
        )
        for cid, cname, passed, score in results_data
    ]
    passed_cnt = sum(1 for _, _, p, _ in results_data if p)
    total_cnt = len(results_data)
    pr = round(passed_cnt / total_cnt, 4) if total_cnt > 0 else 0.0

    run = EvalRun(
        id=run_id,
        suite_id=suite_id,
        agent_id=agent_id,
        agent_version_id=agent_version_id,
        status="completed",
        trigger="manual",
        total_cases=total_cnt,
        passed_cases=passed_cnt,
        failed_cases=total_cnt - passed_cnt,
        pass_rate=pr,
        duration_ms=duration_ms,
        results=results,
    )
    return run


def test_compare_eval_runs_regression() -> None:
    """Identify regression when a previously passing test case fails in candidate."""
    suite_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    v1_id = uuid.uuid4()
    v2_id = uuid.uuid4()

    base_cases = [
        ("case-1", "Valid lead parsing", True, 1.0),
        ("case-2", "Rate limit backoff", True, 1.0),
    ]
    candidate_cases = [
        ("case-1", "Valid lead parsing", True, 1.0),
        ("case-2", "Rate limit backoff", False, 0.0),  # Regressed!
    ]

    base_run = _make_eval_run(suite_id, agent_id, v1_id, base_cases, duration_ms=1000)
    candidate_run = _make_eval_run(suite_id, agent_id, v2_id, candidate_cases, duration_ms=1500)

    report = compare_eval_runs(base_run, candidate_run)

    assert report.status == "regressed"
    assert report.regressions_count == 1
    assert report.improvements_count == 0
    assert report.base_pass_rate == 1.0
    assert report.candidate_pass_rate == 0.5
    assert report.pass_rate_delta == -0.5
    assert report.latency_delta_ms == 500

    regressed_case = next(c for c in report.cases if c.case_id == "case-2")
    assert regressed_case.status == "regressed"
    assert regressed_case.base_passed is True
    assert regressed_case.candidate_passed is False


def test_compare_eval_runs_improvement() -> None:
    """Identify improvement when a previously failing test case passes in candidate."""
    suite_id = uuid.uuid4()
    agent_id = uuid.uuid4()

    base_cases = [
        ("case-1", "JSON format conform", False, 0.0),
        ("case-2", "Security filter", True, 1.0),
    ]
    candidate_cases = [
        ("case-1", "JSON format conform", True, 1.0),  # Improved!
        ("case-2", "Security filter", True, 1.0),
    ]

    base_run = _make_eval_run(suite_id, agent_id, None, base_cases)
    candidate_run = _make_eval_run(suite_id, agent_id, None, candidate_cases)

    report = compare_eval_runs(base_run, candidate_run)

    assert report.status == "improved"
    assert report.regressions_count == 0
    assert report.improvements_count == 1
    assert report.pass_rate_delta == 0.5


def test_compare_eval_runs_unchanged_and_added() -> None:
    """Identify unchanged and newly added test cases."""
    suite_id = uuid.uuid4()
    agent_id = uuid.uuid4()

    base_cases = [
        ("case-1", "Baseline test", True, 1.0),
    ]
    candidate_cases = [
        ("case-1", "Baseline test", True, 1.0),
        ("case-2", "New feature test", True, 1.0),  # Added!
    ]

    base_run = _make_eval_run(suite_id, agent_id, None, base_cases)
    candidate_run = _make_eval_run(suite_id, agent_id, None, candidate_cases)

    report = compare_eval_runs(base_run, candidate_run)

    case2 = next(c for c in report.cases if c.case_id == "case-2")
    assert case2.status == "added"
    assert case2.base_passed is None
    assert case2.candidate_passed is True


@pytest.mark.asyncio
async def test_compare_eval_runs_api_endpoint(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test GET /api/v1/evals/compare endpoint with real database records."""
    agent = Agent(name="compare-agent", owner="engineer@example.com", stage="prototype")
    db_session.add(agent)
    await db_session.flush()

    v1 = AgentVersion(
        agent_id=agent.id,
        version="1.0.0",
        spec={"metadata": {"name": agent.name, "owner": "engineer@example.com"}},
    )
    v2 = AgentVersion(
        agent_id=agent.id,
        version="2.0.0",
        spec={"metadata": {"name": agent.name, "owner": "engineer@example.com"}},
    )
    db_session.add_all([v1, v2])
    await db_session.flush()

    suite = EvalSuite(
        name="Regression Test Suite",
        agent_id=agent.id,
        config={"assertions": []},
    )
    db_session.add(suite)
    await db_session.flush()

    run1 = EvalRun(
        suite_id=suite.id,
        agent_id=agent.id,
        agent_version_id=v1.id,
        status="completed",
        trigger="manual",
        total_cases=2,
        passed_cases=2,
        failed_cases=0,
        pass_rate=1.0,
        duration_ms=1000,
    )
    run2 = EvalRun(
        suite_id=suite.id,
        agent_id=agent.id,
        agent_version_id=v2.id,
        status="completed",
        trigger="manual",
        total_cases=2,
        passed_cases=1,
        failed_cases=1,
        pass_rate=0.5,
        duration_ms=1400,
    )
    db_session.add_all([run1, run2])
    await db_session.flush()

    # Add results
    r1 = EvalResult(
        eval_run_id=run1.id,
        case_id="case-1",
        case_name="Test 1",
        passed=True,
        score=1.0,
        evaluator_name="default",
        evaluator_type="exact_match",
    )
    r2 = EvalResult(
        eval_run_id=run2.id,
        case_id="case-1",
        case_name="Test 1",
        passed=False,  # Regressed
        score=0.0,
        evaluator_name="default",
        evaluator_type="exact_match",
    )
    db_session.add_all([r1, r2])
    await db_session.commit()

    url = f"/api/v1/evals/compare?base_run_id={run1.id}&candidate_run_id={run2.id}"
    resp = await async_client.get(url)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "regressed"
    assert data["regressions_count"] == 1
    assert data["pass_rate_delta"] == -0.5
    assert data["latency_delta_ms"] == 400
    assert len(data["cases"]) == 1
    assert data["cases"][0]["status"] == "regressed"

    # 2. 404 on missing run
    fake_id = uuid.uuid4()
    not_found_resp = await async_client.get(
        f"/api/v1/evals/compare?base_run_id={fake_id}&candidate_run_id={run2.id}"
    )
    assert not_found_resp.status_code == 404
