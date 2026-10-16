"""FastAPI authentication and role-based authorization dependencies."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from identity.models import Identity, Role
from identity.service import authenticate_api_key
from shared.config import get_settings
from shared.db.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

DEV_ADMIN_IDENTITY = Identity(
    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    name="dev-admin",
    role=Role.ADMIN,
    api_key_id=None,
)


def extract_raw_api_key(
    x_api_key: str | None = None,
    authorization: str | None = None,
) -> str | None:
    """Extract raw API key token from headers."""
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()

    if authorization and authorization.strip():
        parts = authorization.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0].lower() in {"bearer", "token"}:
            return parts[1].strip()
        return authorization.strip()

    return None


async def get_current_identity(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> Identity:
    """Authenticate request identity via API key header or fallback to dev admin."""
    settings = get_settings()
    raw_key = extract_raw_api_key(x_api_key, authorization)

    if raw_key is None:
        if settings.auth_enabled:
            detail_msg = (
                "API key required. Provide via 'X-API-Key' or 'Authorization: Bearer <key>'."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_msg,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return DEV_ADMIN_IDENTITY

    key_record = await authenticate_api_key(db, raw_key)
    if key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Identity(
        id=key_record.id,
        name=key_record.name,
        role=Role(key_record.role),
        api_key_id=key_record.id,
    )


def require_role(minimum_role: Role):
    """Dependency factory enforcing caller role hierarchy."""

    async def _role_checker(
        current_identity: Annotated[Identity, Depends(get_current_identity)],
    ) -> Identity:
        if not current_identity.has_role(minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires {minimum_role.value} role.",
            )
        return current_identity

    return _role_checker
