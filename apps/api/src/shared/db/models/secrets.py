"""Encrypted secrets vault database model."""

from __future__ import annotations

import uuid

from shared.db.base import Base, TimestampMixin
from sqlalchemy import String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column


class Secret(Base, TimestampMixin):
    """Encrypted secret stored in the database vault."""

    __tablename__ = "secrets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )
    encrypted_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
