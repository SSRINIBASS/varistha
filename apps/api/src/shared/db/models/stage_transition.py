"""StageTransition database model for immutable lifecycle audit log."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

from shared.db.base import Base, utcnow
from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

if TYPE_CHECKING:
    from shared.db.models.agent import Agent


class StageTransition(Base):
    """Immutable audit record of an agent lifecycle stage transition."""

    __tablename__ = "stage_transitions"

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
    from_stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    to_stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    promoted_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    gate_results: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    # Relationships
    agent: Mapped[Agent] = relationship(
        "Agent",
        back_populates="stage_transitions",
        lazy="selectin",
    )
