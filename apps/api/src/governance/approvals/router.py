"""FastAPI router for governance approval workflow endpoints."""

from __future__ import annotations

import uuid  # noqa: TC003
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from governance.approvals.schemas import (
    ApprovalListResponse,
    ApprovalResolveRequest,
    ApprovalResponse,
)
from governance.approvals.service import (
    ApprovalAlreadyResolvedError,
    ApprovalNotFoundError,
    InvalidApprovalDecisionError,
    get_approval,
    list_approvals,
    resolve_approval,
)
from shared.db.models import Run
from shared.db.session import get_db_session

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])

DbSession = Annotated["AsyncSession", Depends(get_db_session)]


@router.get(
    "",
    response_model=ApprovalListResponse,
    summary="List approval requests",
)
async def list_all_approvals(
    session: DbSession,
    agent_id: Annotated[uuid.UUID | None, Query(description="Filter by agent ID")] = None,
    run_id: Annotated[uuid.UUID | None, Query(description="Filter by run ID")] = None,
    status_filter: Annotated[
        str | None,
        Query(
            alias="status",
            description="Filter by status (pending, approved, rejected, edited)",
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page limit")] = 50,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
) -> ApprovalListResponse:
    """Retrieve paginated approval requests with optional filtering."""
    items, total = await list_approvals(
        session=session,
        agent_id=agent_id,
        run_id=run_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return ApprovalListResponse(
        items=[ApprovalResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    summary="Get approval request details",
)
async def get_approval_by_id(
    approval_id: uuid.UUID,
    session: DbSession,
) -> ApprovalResponse:
    """Retrieve detailed state of an approval request."""
    approval = await get_approval(session, approval_id)
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval '{approval_id}' not found",
        )
    return ApprovalResponse.model_validate(approval)


@router.post(
    "/{approval_id}/resolve",
    response_model=ApprovalResponse,
    summary="Resolve a pending approval request",
)
async def resolve_approval_endpoint(
    approval_id: uuid.UUID,
    payload: ApprovalResolveRequest,
    session: DbSession,
) -> ApprovalResponse:
    """Approve, reject, or edit a pending agent action."""
    try:
        approval = await resolve_approval(
            session=session,
            approval_id=approval_id,
            decision=payload.decision,
            reviewer=payload.reviewer,
            approved_payload=payload.approved_payload,
            feedback=payload.feedback,
        )

        # Synchronize run state if the associated run is waiting for approval
        run = await session.get(Run, approval.run_id)
        if run is not None and run.status == "waiting_approval":
            if payload.decision == "reject":
                run.status = "failed"
                reviewer_note = payload.feedback or "No feedback provided"
                run.error = f"Action rejected by reviewer ({payload.reviewer}): {reviewer_note}"
                run.completed_at = datetime.now(UTC)
            elif payload.decision in ("approve", "edit"):
                # Action approved or edited: update run output and status
                run.status = "completed"
                run.output = {
                    "action": approval.action_type,
                    "tool": approval.tool_name,
                    "payload": approval.approved_payload,
                    "approved_by": approval.reviewer,
                    "feedback": approval.feedback,
                }
                run.completed_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(approval)

        return ApprovalResponse.model_validate(approval)

    except ApprovalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ApprovalAlreadyResolvedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidApprovalDecisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
