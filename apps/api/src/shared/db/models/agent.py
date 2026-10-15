"""Agent and AgentVersion database models."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

from shared.db.base import Base, TimestampMixin, utcnow
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

if TYPE_CHECKING:
    from shared.db.models.approval import Approval
    from shared.db.models.run import Run
    from shared.db.models.stage_transition import StageTransition


class Agent(Base, TimestampMixin):
    """Registered AI employee agent definition."""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    owner: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        String(32),
        default="draft",
        nullable=False,
    )
    current_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # Relationships
    versions: Mapped[list[AgentVersion]] = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="desc(AgentVersion.created_at)",
        lazy="selectin",
    )
    runs: Mapped[list[Run]] = relationship(
        "Run",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    stage_transitions: Mapped[list[StageTransition]] = relationship(
        "StageTransition",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="desc(StageTransition.created_at)",
        lazy="selectin",
    )
    approvals: Mapped[list[Approval]] = relationship(
        "Approval",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="desc(Approval.created_at)",
        lazy="selectin",
    )


class AgentVersion(Base):
    """Immutable snapshot of an AgentSpec for an agent version."""

    __tablename__ = "agent_versions"
    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "version",
            name="uq_agent_versions_agent_id_version",
        ),
    )

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
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    spec: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    # Relationships
    agent: Mapped[Agent] = relationship(
        "Agent",
        back_populates="versions",
        lazy="selectin",
    )
    runs: Mapped[list[Run]] = relationship(
        "Run",
        back_populates="agent_version",
        lazy="selectin",
    )
