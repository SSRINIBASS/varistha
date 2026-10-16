"""Service logic for API key generation, hashing, and authentication."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from shared.db.models.identity import ApiKey
from sqlalchemy import select

if TYPE_CHECKING:
    from identity.schemas import CreateApiKeyRequest
    from sqlalchemy.ext.asyncio import AsyncSession


def generate_key_material() -> tuple[str, str, str]:
    """Generate plaintext API key, display prefix, and SHA-256 hash.

    Returns:
        tuple[str, str, str]: (raw_key, prefix, key_hash)

    """
    token = secrets.token_urlsafe(24)
    raw_key = f"var_live_{token}"
    prefix = raw_key[:14]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, prefix, key_hash


def hash_key(raw_key: str) -> str:
    """Compute deterministic SHA-256 hash of an API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def create_api_key(
    db: AsyncSession,
    request: CreateApiKeyRequest,
) -> tuple[ApiKey, str]:
    """Create and persist a new API key record.

    Returns:
        tuple[ApiKey, str]: The persisted DB record and the plaintext key.

    """
    raw_key, prefix, key_hash = generate_key_material()

    expires_at: datetime | None = None
    if request.expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=request.expires_in_days)

    api_key = ApiKey(
        id=uuid.uuid4(),
        name=request.name,
        prefix=prefix,
        key_hash=key_hash,
        role=request.role.value,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, raw_key


async def list_api_keys(db: AsyncSession) -> list[ApiKey]:
    """List all API keys ordered by creation date."""
    query = select(ApiKey).order_by(ApiKey.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_api_key_by_id(db: AsyncSession, key_id: uuid.UUID) -> ApiKey | None:
    """Retrieve an API key by unique identifier."""
    query = select(ApiKey).where(ApiKey.id == key_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def revoke_api_key(db: AsyncSession, key_id: uuid.UUID) -> bool:
    """Revoke an API key immediately.

    Returns:
        bool: True if key was found and revoked, False otherwise.

    """
    key = await get_api_key_by_id(db, key_id)
    if key is None or key.revoked_at is not None:
        return False

    key.revoked_at = datetime.now(UTC)
    await db.commit()
    return True


async def authenticate_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    """Verify raw API key against stored SHA-256 hash and check active status.

    Returns:
        ApiKey | None: Active ApiKey record if authenticated, None otherwise.

    """
    key_hash = hash_key(raw_key.strip())
    query = select(ApiKey).where(ApiKey.key_hash == key_hash)
    result = await db.execute(query)
    key = result.scalar_one_or_none()

    if key is None or not key.is_active:
        return None

    # Update last_used_at timestamp
    key.last_used_at = datetime.now(UTC)
    await db.commit()
    return key
