"""System settings model for platform-wide state such as the global kill switch."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from shared.db.base import Base, utcnow
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON


class SystemSetting(Base):
    """Platform-wide system configuration and operational state."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    value: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
