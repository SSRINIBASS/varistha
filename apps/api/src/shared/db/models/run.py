"""Run database model."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

from shared.db.base import Base, TimestampMixin
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

if TYPE_CHECKING:
    from shared.db.models.agent import Agent, AgentVersion
    from shared.db.models.approval import Approval
    from shared.db.models.span import Span


class Run(Base, TimestampMixin):
    """Single execution of an AI agent."""

    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    agent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("agent_versions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        index=True,
        nullable=False,
    )
    trigger_type: Mapped[str] = mapped_column(
        String(32),
        default="manual",
        nullable=False,
    )
    input: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    output: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    agent: Mapped[Agent] = relationship(
        "Agent",
        back_populates="runs",
        lazy="selectin",
    )
    agent_version: Mapped[AgentVersion | None] = relationship(
        "AgentVersion",
        back_populates="runs",
        lazy="selectin",
    )
    spans: Mapped[list[Span]] = relationship(
        "Span",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="Span.start_time.asc()",
        lazy="selectin",
    )
    approvals: Mapped[list[Approval]] = relationship(
        "Approval",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="Approval.created_at.asc()",
        lazy="selectin",
    )
