"""Service layer for human-in-the-loop governance approvals and payload diffing."""

from __future__ import annotations

import uuid  # noqa: TC003
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from shared.db.models import Approval
from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ApprovalNotFoundError(Exception):
    """Raised when an approval record cannot be located."""


class ApprovalAlreadyResolvedError(Exception):
    """Raised when an approval is already approved, rejected, or edited."""


class InvalidApprovalDecisionError(Exception):
    """Raised when an invalid resolution decision is provided."""


def compute_payload_diff(
    proposed: dict[str, Any],
    approved: dict[str, Any],
) -> dict[str, Any]:
    """Compute a recursive field-level JSON diff between proposed and approved payloads.

    Returns a dict with 'added', 'removed', and 'modified' structures.
    """
    added: dict[str, Any] = {}
    removed: dict[str, Any] = {}
    modified: dict[str, Any] = {}

    proposed_keys = set(proposed.keys())
    approved_keys = set(approved.keys())

    # Detect additions
    for key in approved_keys - proposed_keys:
        added[key] = approved[key]

    # Detect removals
    for key in proposed_keys - approved_keys:
        removed[key] = proposed[key]

    # Detect modifications / deep diffs
    for key in proposed_keys & approved_keys:
        old_val = proposed[key]
        new_val = approved[key]

        if isinstance(old_val, dict) and isinstance(new_val, dict):
            nested_diff = compute_payload_diff(old_val, new_val)
            if nested_diff["added"] or nested_diff["removed"] or nested_diff["modified"]:
                modified[key] = nested_diff
        elif old_val != new_val:
            modified[key] = {
                "old": old_val,
                "new": new_val,
            }

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
    }


async def create_approval(
    session: AsyncSession,
    run_id: uuid.UUID,
    agent_id: uuid.UUID,
    action_type: str,
    proposed_payload: dict[str, Any],
    tool_name: str | None = None,
    description: str | None = None,
) -> Approval:
    """Create a new pending approval record."""
    approval = Approval(
        run_id=run_id,
        agent_id=agent_id,
        status="pending",
        action_type=action_type,
        tool_name=tool_name,
        description=description,
        proposed_payload=proposed_payload,
        created_at=datetime.now(UTC),
    )
    session.add(approval)
    await session.commit()
    await session.refresh(approval)
    return approval


async def get_approval(
    session: AsyncSession,
    approval_id: uuid.UUID,
) -> Approval | None:
    """Retrieve an approval record by UUID."""
    stmt = select(Approval).where(Approval.id == approval_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_approvals(
    session: AsyncSession,
    agent_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Approval], int]:
    """List approvals with optional filters and pagination."""
    count_stmt = select(func.count(Approval.id))
    query = select(Approval).order_by(Approval.created_at.desc())

    if agent_id is not None:
        count_stmt = count_stmt.where(Approval.agent_id == agent_id)
        query = query.where(Approval.agent_id == agent_id)

    if run_id is not None:
        count_stmt = count_stmt.where(Approval.run_id == run_id)
        query = query.where(Approval.run_id == run_id)

    if status is not None:
        count_stmt = count_stmt.where(Approval.status == status)
        query = query.where(Approval.status == status)

    count_res = await session.execute(count_stmt)
    total = count_res.scalar_one()

    query = query.limit(limit).offset(offset)
    res = await session.execute(query)
    approvals = list(res.scalars().all())

    return approvals, total


async def resolve_approval(
    session: AsyncSession,
    approval_id: uuid.UUID,
    decision: str,
    reviewer: str,
    approved_payload: dict[str, Any] | None = None,
    feedback: str | None = None,
) -> Approval:
    """Resolve a pending approval request with approve, reject, or edit."""
    approval = await get_approval(session, approval_id)
    if approval is None:
        raise ApprovalNotFoundError(f"Approval '{approval_id}' not found")

    if approval.status != "pending":
        raise ApprovalAlreadyResolvedError(
            f"Approval '{approval_id}' is already {approval.status} and cannot be resolved again."
        )

    now = datetime.now(UTC)
    approval.reviewer = reviewer
    approval.feedback = feedback
    approval.resolved_at = now

    if decision == "approve":
        approval.status = "approved"
        approval.approved_payload = approval.proposed_payload
        approval.diff = None
    elif decision == "reject":
        approval.status = "rejected"
        approval.approved_payload = None
        approval.diff = None
    elif decision == "edit":
        approval.status = "edited"
        final_payload = approved_payload if approved_payload is not None else {}
        approval.approved_payload = final_payload
        approval.diff = compute_payload_diff(approval.proposed_payload, final_payload)
    else:
        raise InvalidApprovalDecisionError(
            f"Invalid decision '{decision}'. Expected 'approve', 'reject', or 'edit'."
        )

    await session.commit()
    await session.refresh(approval)
    return approval
