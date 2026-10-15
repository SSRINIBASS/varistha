"""Pydantic schemas for the Agent Runtime & Run execution API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunCreateRequest(BaseModel):
    """Payload to trigger an agent execution run."""

    input: dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters or query payload provided to the agent.",
    )
    trigger_type: str = Field(
        default="manual",
        description="Type of trigger that started the run (manual, schedule, webhook).",
    )


class RunResponse(BaseModel):
    """Public representation of an agent execution run."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    agent_version_id: uuid.UUID | None = None
    status: str = Field(
        description="Run execution state (pending, running, completed, failed, waiting_approval).",
    )
    trigger_type: str = Field(description="Trigger type that initiated the run.")
    input: dict[str, Any] | None = Field(default=None, description="Input data passed to the run.")
    output: dict[str, Any] | None = Field(
        default=None,
        description="Output payload produced by the agent run.",
    )
    error: str | None = Field(default=None, description="Failure error message if run failed.")
    started_at: datetime | None = Field(default=None, description="Timestamp when execution began.")
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when execution ended.",
    )
    cost_usd: float = Field(default=0.0, description="Estimated total cost in USD.")
    total_tokens: int = Field(default=0, description="Total tokens consumed.")
    created_at: datetime
    updated_at: datetime


class RunListResponse(BaseModel):
    """Paginated list of agent runs."""

    items: list[RunResponse]
    total: int
    limit: int
    offset: int
