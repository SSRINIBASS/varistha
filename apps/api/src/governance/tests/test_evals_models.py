"""Unit tests for Eval database models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from shared.db.models.agent import Agent, AgentVersion
from shared.db.models.eval import EvalResult, EvalRun, EvalSuite
from sqlalchemy import select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_eval_suite_and_run_cascade(db_session: AsyncSession) -> None:
    agent = Agent(
        name="lead-researcher",
        owner="operator@varistha.io",
        stage="prototype",
    )
    db_session.add(agent)
    await db_session.flush()

    version = AgentVersion(
        agent_id=agent.id,
        version="1.0.0",
        spec={"apiVersion": "varistha/v1", "kind": "Agent"},
    )
    db_session.add(version)
    await db_session.flush()

    suite = EvalSuite(
        name="lead-eval-suite",
        agent_id=agent.id,
        description="Lead qualification evaluations",
        config={"evaluators": [{"name": "check-name", "type": "contains"}]},
    )
    db_session.add(suite)
    await db_session.flush()

    assert suite.id is not None
    assert suite.created_at is not None

    run = EvalRun(
        suite_id=suite.id,
        agent_id=agent.id,
        agent_version_id=version.id,
        status="running",
        trigger="manual",
    )
    db_session.add(run)
    await db_session.flush()

    res1 = EvalResult(
        eval_run_id=run.id,
        case_id="case-1",
        case_name="Valid lead input",
        input_data={"company": "Acme Corp"},
        expected_output={"qualified": True},
        actual_output={"qualified": True},
        passed=True,
        score=1.0,
        evaluator_name="contains-check",
        evaluator_type="contains",
    )
    res2 = EvalResult(
        eval_run_id=run.id,
        case_id="case-2",
        case_name="Missing email input",
        input_data={"company": ""},
        expected_output={"qualified": False},
        actual_output={"qualified": True},
        passed=False,
        score=0.0,
        evaluator_name="contains-check",
        evaluator_type="contains",
        failure_reason="Expected False but received True",
    )
    db_session.add_all([res1, res2])
    await db_session.flush()

    # Query run and verify results relationship
    stmt = select(EvalRun).where(EvalRun.id == run.id)
    retrieved = (await db_session.execute(stmt)).scalars().first()
    assert retrieved is not None
    assert len(retrieved.results) == 2
    assert retrieved.results[0].passed is True
    assert retrieved.results[1].passed is False

    # Verify agent back_populates
    agent_reloaded = (
        (
            await db_session.execute(
                select(Agent)
                .options(selectinload(Agent.eval_suites), selectinload(Agent.eval_runs))
                .where(Agent.id == agent.id)
            )
        )
        .scalars()
        .first()
    )
    assert agent_reloaded is not None
    assert len(agent_reloaded.eval_suites) == 1
    assert len(agent_reloaded.eval_runs) == 1

    # Delete suite and check cascade deletion on run and results
    await db_session.delete(suite)
    await db_session.flush()

    runs_check = (
        (await db_session.execute(select(EvalRun).where(EvalRun.id == run.id))).scalars().all()
    )
    assert len(runs_check) == 0

    results_check = (
        (await db_session.execute(select(EvalResult).where(EvalResult.eval_run_id == run.id)))
        .scalars()
        .all()
    )
    assert len(results_check) == 0
