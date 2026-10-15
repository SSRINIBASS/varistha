"""Pydantic schemas for the Human-in-the-Loop Approval Workflow."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApprovalResponse(BaseModel):
    """API representation of an approval request record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique approval identifier")
    run_id: uuid.UUID = Field(
        ..., description="ID of the execution run that triggered this approval"
    )
    agent_id: uuid.UUID = Field(..., description="ID of the agent requesting action")
    status: Literal["pending", "approved", "rejected", "edited"] = Field(
        ..., description="Current status of the approval request"
    )
    action_type: str = Field(
        ..., description="Category of action (e.g. 'tool_call', 'outbound_action')"
    )
    tool_name: str | None = Field(
        None, description="Specific tool or plugin requested, if applicable"
    )
    description: str | None = Field(None, description="Human-readable context or explanation")
    proposed_payload: dict[str, Any] = Field(
        ..., description="Original payload proposed by the model"
    )
    approved_payload: dict[str, Any] | None = Field(
        None, description="Final payload approved for execution by human reviewer"
    )
    diff: dict[str, Any] | None = Field(
        None, description="Field-level JSON diff between proposed and approved payloads"
    )
    feedback: str | None = Field(None, description="Reviewer feedback or explanation")
    reviewer: str | None = Field(
        None, description="Identifier of the reviewer who resolved the request"
    )
    created_at: datetime = Field(..., description="Timestamp when approval request was created")
    resolved_at: datetime | None = Field(None, description="Timestamp when approval was resolved")


class ApprovalListResponse(BaseModel):
    """Paginated list of approval requests."""

    items: list[ApprovalResponse] = Field(..., description="List of approval records")
    total: int = Field(..., description="Total count matching filter criteria")
    limit: int = Field(..., description="Page limit applied")
    offset: int = Field(..., description="Page offset applied")


class ApprovalResolveRequest(BaseModel):
    """Payload to resolve a pending approval request."""

    decision: Literal["approve", "reject", "edit"] = Field(
        ..., description="Resolution decision: 'approve', 'reject', or 'edit'"
    )
    reviewer: str = Field(
        ..., min_length=1, description="Identifier of the operator resolving the approval"
    )
    approved_payload: dict[str, Any] | None = Field(
        None, description="Modified payload if decision is 'edit' or custom approved payload"
    )
    feedback: str | None = Field(
        None, description="Operator notes or reasoning provided to evaluate or guide the agent"
    )
