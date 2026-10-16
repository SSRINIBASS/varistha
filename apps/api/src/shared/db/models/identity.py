"""Identity and API Key database models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from shared.db.base import Base, TimestampMixin
from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column


class ApiKey(Base, TimestampMixin):
    """API key for programmatic authentication and role authorization."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="operator")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_active(self) -> bool:
        """Check if the API key is active and not revoked or expired."""
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None:
            expires = self.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            return expires > now
        return True
