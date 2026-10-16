"""Database service for encrypted secrets vault management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.crypto import decrypt_secret, encrypt_secret
from shared.db.models.secrets import Secret
from sqlalchemy import select

if TYPE_CHECKING:
    from collections.abc import Sequence

    from identity.schemas import CreateSecretRequest
    from sqlalchemy.ext.asyncio import AsyncSession


async def store_secret(
    db: AsyncSession,
    request: CreateSecretRequest,
) -> Secret:
    """Encrypt and store or update a secret in the vault."""
    encrypted_payload = encrypt_secret(request.value)

    stmt = select(Secret).where(Secret.name == request.name)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is not None:
        existing.encrypted_value = encrypted_payload
        if request.description is not None:
            existing.description = request.description
        await db.commit()
        await db.refresh(existing)
        return existing

    new_secret = Secret(
        name=request.name,
        encrypted_value=encrypted_payload,
        description=request.description,
    )
    db.add(new_secret)
    await db.commit()
    await db.refresh(new_secret)
    return new_secret


async def resolve_secret(
    db: AsyncSession,
    name: str,
) -> str | None:
    """Retrieve and decrypt a stored secret by name, returning None if absent."""
    stmt = select(Secret).where(Secret.name == name)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        return None
    return decrypt_secret(record.encrypted_value)


async def list_secrets(
    db: AsyncSession,
) -> Sequence[Secret]:
    """List all secret metadata from the vault."""
    stmt = select(Secret).order_by(Secret.name)
    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_secret(
    db: AsyncSession,
    name: str,
) -> bool:
    """Delete a secret from the vault by name."""
    stmt = select(Secret).where(Secret.name == name)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        return False

    await db.delete(record)
    await db.commit()
    return True
