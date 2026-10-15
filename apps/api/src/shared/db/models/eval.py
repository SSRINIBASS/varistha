"""Database models for evaluation suites, runs, and granular results."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

from shared.db.base import Base, utcnow
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

if TYPE_CHECKING:
    from shared.db.models.agent import Agent, AgentVersion


class EvalSuite(Base):
    """Evaluation suite specification and test cases for an agent."""

    __tablename__ = "eval_suites"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    # Relationships
    agent: Mapped[Agent] = relationship(
        "Agent",
        back_populates="eval_suites",
        lazy="selectin",
    )
    runs: Mapped[list[EvalRun]] = relationship(
        "EvalRun",
        back_populates="suite",
        cascade="all, delete-orphan",
        order_by="desc(EvalRun.created_at)",
        lazy="selectin",
    )


class EvalRun(Base):
    """An execution instance of an evaluation suite against an agent version."""

    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    suite_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("eval_suites.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
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
    )  # pending, running, completed, failed
    trigger: Mapped[str] = mapped_column(
        String(32),
        default="manual",
        nullable=False,
    )  # manual, version_change, ci, schedule
    pass_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    total_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    passed_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    failed_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    suite: Mapped[EvalSuite] = relationship(
        "EvalSuite",
        back_populates="runs",
        lazy="selectin",
    )
    agent: Mapped[Agent] = relationship(
        "Agent",
        back_populates="eval_runs",
        lazy="selectin",
    )
    version: Mapped[AgentVersion | None] = relationship(
        "AgentVersion",
        lazy="selectin",
    )
    results: Mapped[list[EvalResult]] = relationship(
        "EvalResult",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EvalResult(Base):
    """Granular per-test-case assertion result in an evaluation run."""

    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    eval_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("eval_runs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    case_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    case_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    expected_output: Mapped[Any | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    actual_output: Mapped[Any | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    evaluator_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    evaluator_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    tokens_used: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    # Relationships
    run: Mapped[EvalRun] = relationship(
        "EvalRun",
        back_populates="results",
        lazy="selectin",
    )
