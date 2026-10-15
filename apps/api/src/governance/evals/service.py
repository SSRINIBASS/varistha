"""Service layer for evaluation suites, runs, and results management."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import TYPE_CHECKING

from shared.db.base import utcnow
from shared.db.models.eval import EvalResult, EvalRun, EvalSuite
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from governance.evals.schemas import EvalResultCreate, EvalRunCreate, EvalSuiteCreate
    from sqlalchemy.ext.asyncio import AsyncSession


async def create_or_update_eval_suite(
    db: AsyncSession,
    data: EvalSuiteCreate,
) -> EvalSuite:
    """Create or update an evaluation suite definition."""
    stmt = select(EvalSuite).where(
        EvalSuite.agent_id == data.agent_id,
        EvalSuite.name == data.name,
    )
    result = await db.execute(stmt)
    suite = result.scalars().first()

    if suite:
        suite.description = data.description
        suite.config = data.config
        suite.updated_at = utcnow()
    else:
        suite = EvalSuite(
            name=data.name,
            agent_id=data.agent_id,
            description=data.description,
            config=data.config,
        )
        db.add(suite)

    await db.flush()
    await db.refresh(suite)
    return suite


async def get_eval_suite(
    db: AsyncSession,
    suite_id: uuid.UUID,
) -> EvalSuite | None:
    """Get an evaluation suite by UUID."""
    stmt = select(EvalSuite).where(EvalSuite.id == suite_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_eval_suites(
    db: AsyncSession,
    agent_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EvalSuite], int]:
    """List evaluation suites with pagination and optional agent filtering."""
    query = select(EvalSuite)
    count_query = select(func.count(EvalSuite.id))

    if agent_id:
        query = query.where(EvalSuite.agent_id == agent_id)
        count_query = count_query.where(EvalSuite.agent_id == agent_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(EvalSuite.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    suites = list(res.scalars().all())

    return suites, total


async def create_eval_run(
    db: AsyncSession,
    data: EvalRunCreate,
) -> EvalRun:
    """Initiate an evaluation run record."""
    suite = await get_eval_suite(db, data.suite_id)
    if not suite:
        msg = f"Evaluation suite with id '{data.suite_id}' not found."
        raise ValueError(msg)

    run = EvalRun(
        suite_id=suite.id,
        agent_id=suite.agent_id,
        agent_version_id=data.agent_version_id,
        trigger=data.trigger,
        status="running",
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def record_eval_results(
    db: AsyncSession,
    eval_run_id: uuid.UUID,
    results: list[EvalResultCreate],
    duration_ms: int | None = None,
    error_message: str | None = None,
) -> EvalRun:
    """Record assertions results and finalize eval run metrics."""
    run = await get_eval_run(db, eval_run_id)
    if not run:
        msg = f"Eval run with id '{eval_run_id}' not found."
        raise ValueError(msg)

    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    pass_rate = (passed_count / total_count) if total_count > 0 else 0.0

    for res in results:
        eval_result = EvalResult(
            eval_run_id=eval_run_id,
            case_id=res.case_id,
            case_name=res.case_name,
            input_data=res.input_data,
            expected_output=res.expected_output,
            actual_output=res.actual_output,
            passed=res.passed,
            score=res.score,
            evaluator_name=res.evaluator_name,
            evaluator_type=res.evaluator_type,
            failure_reason=res.failure_reason,
            latency_ms=res.latency_ms,
            tokens_used=res.tokens_used,
        )
        db.add(eval_result)

    run.total_cases = total_count
    run.passed_cases = passed_count
    run.failed_cases = total_count - passed_count
    run.pass_rate = pass_rate
    run.duration_ms = duration_ms
    run.error_message = error_message
    run.status = "failed" if error_message else "completed"
    run.completed_at = utcnow()

    await db.flush()
    await db.refresh(run)
    return run


async def get_eval_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> EvalRun | None:
    """Get an evaluation run by UUID, including granular assertion results."""
    stmt = select(EvalRun).options(selectinload(EvalRun.results)).where(EvalRun.id == run_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_eval_runs(
    db: AsyncSession,
    agent_id: uuid.UUID | None = None,
    suite_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EvalRun], int]:
    """List evaluation runs with optional filtering by agent or suite."""
    query = select(EvalRun)
    count_query = select(func.count(EvalRun.id))

    if agent_id:
        query = query.where(EvalRun.agent_id == agent_id)
        count_query = count_query.where(EvalRun.agent_id == agent_id)

    if suite_id:
        query = query.where(EvalRun.suite_id == suite_id)
        count_query = count_query.where(EvalRun.suite_id == suite_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(EvalRun.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    runs = list(res.scalars().all())

    return runs, total
