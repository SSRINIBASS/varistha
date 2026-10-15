"""REST API router for evaluation suites and runs under /api/v1/evals."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from governance.evals import service
from governance.evals.schemas import (
    EvalResultCreate,
    EvalRunCreate,
    EvalRunDetailResponse,
    EvalRunListResponse,
    EvalRunResponse,
    EvalSuiteCreate,
    EvalSuiteListResponse,
    EvalSuiteResponse,
)
from shared.db.session import get_db_session

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/evals", tags=["Governance / Evals"])

DbSession = Annotated["AsyncSession", Depends(get_db_session)]


@router.post(
    "/suites",
    response_model=EvalSuiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register or update an evaluation suite",
)
async def create_eval_suite(
    payload: EvalSuiteCreate,
    db: DbSession,
) -> EvalSuiteResponse:
    """Register or update an eval suite definition for an agent."""
    suite = await service.create_or_update_eval_suite(db, payload)
    return EvalSuiteResponse.model_validate(suite)


@router.get(
    "/suites",
    response_model=EvalSuiteListResponse,
    summary="List evaluation suites",
)
async def list_eval_suites(
    db: DbSession,
    agent_id: Annotated[uuid.UUID | None, Query(description="Filter by agent UUID")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EvalSuiteListResponse:
    """List evaluation suites with pagination and optional agent filtering."""
    suites, total = await service.list_eval_suites(
        db, agent_id=agent_id, limit=limit, offset=offset
    )
    return EvalSuiteListResponse(
        suites=[EvalSuiteResponse.model_validate(s) for s in suites],
        total=total,
    )


@router.get(
    "/suites/{suite_id}",
    response_model=EvalSuiteResponse,
    summary="Get an evaluation suite by UUID",
)
async def get_eval_suite(
    suite_id: uuid.UUID,
    db: DbSession,
) -> EvalSuiteResponse:
    """Retrieve details of an evaluation suite."""
    suite = await service.get_eval_suite(db, suite_id)
    if not suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Eval suite '{suite_id}' not found.",
        )
    return EvalSuiteResponse.model_validate(suite)


@router.post(
    "/runs",
    response_model=EvalRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate an evaluation run",
)
async def create_eval_run(
    payload: EvalRunCreate,
    db: DbSession,
) -> EvalRunResponse:
    """Start an evaluation run for a suite."""
    try:
        run = await service.create_eval_run(db, payload)
        return EvalRunResponse.model_validate(run)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.post(
    "/runs/{run_id}/results",
    response_model=EvalRunDetailResponse,
    summary="Record evaluation results and finalize run",
)
async def record_eval_results(
    run_id: uuid.UUID,
    results: list[EvalResultCreate],
    db: DbSession,
    duration_ms: Annotated[int | None, Query()] = None,
    error_message: Annotated[str | None, Query()] = None,
) -> EvalRunDetailResponse:
    """Record assertions results and finalize metrics for an eval run."""
    try:
        run = await service.record_eval_results(
            db,
            eval_run_id=run_id,
            results=results,
            duration_ms=duration_ms,
            error_message=error_message,
        )
        return EvalRunDetailResponse.model_validate(run)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/runs",
    response_model=EvalRunListResponse,
    summary="List evaluation runs",
)
async def list_eval_runs(
    db: DbSession,
    agent_id: Annotated[uuid.UUID | None, Query(description="Filter by agent UUID")] = None,
    suite_id: Annotated[uuid.UUID | None, Query(description="Filter by suite UUID")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EvalRunListResponse:
    """List evaluation runs with pagination and optional filters."""
    runs, total = await service.list_eval_runs(
        db,
        agent_id=agent_id,
        suite_id=suite_id,
        limit=limit,
        offset=offset,
    )
    return EvalRunListResponse(
        runs=[EvalRunResponse.model_validate(r) for r in runs],
        total=total,
    )


@router.get(
    "/runs/{run_id}",
    response_model=EvalRunDetailResponse,
    summary="Get evaluation run details with granular assertion results",
)
async def get_eval_run(
    run_id: uuid.UUID,
    db: DbSession,
) -> EvalRunDetailResponse:
    """Retrieve details and assertion results for an evaluation run."""
    run = await service.get_eval_run(db, run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Eval run '{run_id}' not found.",
        )
    return EvalRunDetailResponse.model_validate(run)
