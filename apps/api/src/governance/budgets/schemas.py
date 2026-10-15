"""Pydantic schemas for budget tracking and kill switch circuit breakers."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AgentBudgetStatusResponse(BaseModel):
    """Current financial spend and circuit-breaker status for an agent."""

    model_config = ConfigDict(from_attributes=True)

    agent_id: uuid.UUID
    agent_name: str
    is_active: bool
    kill_switch_tripped: bool
    kill_switch_reason: str | None = None
    kill_switch_tripped_at: datetime | None = None
    max_usd_per_run: float | None = None
    max_usd_per_day: float | None = None
    daily_spend_usd: Annotated[float, Field(ge=0.0)] = 0.0
    daily_runs_count: Annotated[int, Field(ge=0)] = 0
    daily_budget_remaining_usd: float | None = None
    daily_budget_utilization_pct: float | None = None


class KillSwitchRequest(BaseModel):
    """Payload to trip or configure an agent kill switch."""

    reason: str = Field(
        ...,
        min_length=1,
        description="Reason for tripping the emergency kill switch.",
    )
    operator: str | None = Field(
        default="system",
        description="Operator identity tripping the switch.",
    )


class KillSwitchResponse(BaseModel):
    """Result of tripping or resetting an agent kill switch."""

    agent_id: uuid.UUID
    agent_name: str
    is_active: bool
    kill_switch_tripped: bool
    reason: str | None = None
    tripped_at: datetime | None = None
    operator: str | None = None


class GlobalKillSwitchRequest(BaseModel):
    """Payload to toggle the control plane-wide global kill switch."""

    enabled: bool = Field(..., description="Whether the global emergency stop is active.")
    reason: str | None = Field(
        default=None,
        description="Reason for toggling global emergency stop.",
    )
    operator: str | None = Field(
        default="system",
        description="Operator identity toggling the switch.",
    )


class GlobalKillSwitchStatus(BaseModel):
    """System-level operational status of the global emergency stop."""

    enabled: bool
    reason: str | None = None
    tripped_at: str | None = None
    operator: str | None = None
