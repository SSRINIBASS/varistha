"""Span database model for OTLP-derived trace spans."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

from shared.db.base import Base, utcnow
from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

if TYPE_CHECKING:
    from shared.db.models.run import Run


class Span(Base):
    """Execution span representing an LLM call, tool call, or lifecycle step."""

    __tablename__ = "spans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    trace_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    span_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    parent_span_id: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(32),
        default="INTERNAL",
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="UNSET",
        nullable=False,
    )
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    events: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    # Relationships
    run: Mapped[Run] = relationship(
        "Run",
        back_populates="spans",
        lazy="selectin",
    )
