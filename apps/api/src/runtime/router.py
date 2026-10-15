"""FastAPI router for Agent Runtime and Run execution endpoints."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from runtime.adapter import LangGraphRuntime
from runtime.interface import Runtime
from runtime.schemas import RunCreateRequest, RunListResponse, RunResponse
from runtime.service import (
    AgentNotFoundError,
    NoVersionFoundError,
    get_run,
    list_runs_for_agent,
    resolve_agent,
    trigger_agent_run,
)
from shared.db.session import get_db_session

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["runs"])

_default_runtime = LangGraphRuntime()


def get_runtime() -> Runtime:
    """Dependency provider for the execution Runtime engine."""
    return _default_runtime


DbSession = Annotated["AsyncSession", Depends(get_db_session)]
RuntimeDep = Annotated[Runtime, Depends(get_runtime)]


@router.post(
    "/api/v1/agents/{id_or_name}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an agent run",
)
async def trigger_run(
    id_or_name: str,
    payload: RunCreateRequest,
    session: DbSession,
    runtime: RuntimeDep,
) -> RunResponse:
    """Trigger execution of an agent and return the run outcome."""
    try:
        run = await trigger_agent_run(
            session=session,
            id_or_name=id_or_name,
            input_data=payload.input,
            trigger_type=payload.trigger_type,
            runtime=runtime,
        )
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except NoVersionFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return RunResponse.model_validate(run)


@router.get(
    "/api/v1/agents/{id_or_name}/runs",
    response_model=RunListResponse,
    summary="List runs for an agent",
)
async def get_agent_runs(
    id_or_name: str,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset.")] = 0,
) -> RunListResponse:
    """List historical execution runs for an agent."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    runs, total = await list_runs_for_agent(session, agent.id, limit=limit, offset=offset)
    items = [RunResponse.model_validate(r) for r in runs]

    return RunListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/api/v1/runs/{run_id}",
    response_model=RunResponse,
    summary="Get run details",
)
async def get_run_detail(
    run_id: uuid.UUID,
    session: DbSession,
) -> RunResponse:
    """Retrieve execution status, inputs, outputs, tokens, and cost for a run."""
    run = await get_run(session, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    return RunResponse.model_validate(run)
