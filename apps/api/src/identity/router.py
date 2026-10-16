"""REST API endpoints for authentication and API key management."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from identity.dependencies import get_current_identity, require_role
from identity.models import Identity, Role
from identity.schemas import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreatedApiKeyResponse,
    CreateSecretRequest,
    CurrentIdentityResponse,
    SecretMetadataResponse,
    SecretValueResponse,
)
from identity.secrets_service import (
    delete_secret,
    list_secrets,
    resolve_secret,
    store_secret,
)
from identity.service import create_api_key, list_api_keys, revoke_api_key
from shared.db.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

router = APIRouter(prefix="/api/v1/auth", tags=["Identity & Auth"])


@router.post(
    "/keys",
    response_model=CreatedApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key (Admin only)",
)
async def create_new_key(
    request: CreateApiKeyRequest,
    _: Annotated[Identity, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CreatedApiKeyResponse:
    """Issue a new API key with the specified role."""
    api_key, raw_key = await create_api_key(db, request)
    return CreatedApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        role=Role(api_key.role),
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        is_active=api_key.is_active,
        raw_key=raw_key,
    )


@router.get(
    "/keys",
    response_model=list[ApiKeyResponse],
    summary="List all API keys (Admin only)",
)
async def list_keys(
    _: Annotated[Identity, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ApiKeyResponse]:
    """Retrieve metadata of all issued API keys."""
    keys = await list_api_keys(db)
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            prefix=k.prefix,
            role=Role(k.role),
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
            is_active=k.is_active,
        )
        for k in keys
    ]


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke an API key (Admin only)",
)
async def delete_key(
    key_id: uuid.UUID,
    _: Annotated[Identity, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str | bool]:
    """Revoke an API key immediately."""
    revoked = await revoke_api_key(db, key_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key '{key_id}' not found or already revoked.",
        )
    return {"revoked": True, "key_id": str(key_id)}


@router.get(
    "/me",
    response_model=CurrentIdentityResponse,
    summary="Get current authenticated identity",
)
async def get_me(
    current_identity: Annotated[Identity, Depends(get_current_identity)],
) -> CurrentIdentityResponse:
    """Return the authenticated caller identity and role."""
    return CurrentIdentityResponse(
        id=current_identity.id,
        name=current_identity.name,
        role=current_identity.role,
        api_key_id=current_identity.api_key_id,
    )


@router.post(
    "/secrets",
    response_model=SecretMetadataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store or update a secret in the encrypted vault (Admin only)",
)
async def create_or_update_secret(
    request: CreateSecretRequest,
    _: Annotated[Identity, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecretMetadataResponse:
    """Store or rotate a secret value encrypted at rest using AES-256-GCM."""
    record = await store_secret(db, request)
    return SecretMetadataResponse(
        id=record.id,
        name=record.name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get(
    "/secrets",
    response_model=list[SecretMetadataResponse],
    summary="List all stored secrets metadata (Operator or Admin)",
)
async def list_vault_secrets(
    _: Annotated[Identity, Depends(require_role(Role.OPERATOR))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SecretMetadataResponse]:
    """Retrieve metadata of all stored secrets without exposing decrypted values."""
    records = await list_secrets(db)
    return [
        SecretMetadataResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.get(
    "/secrets/{name}",
    response_model=SecretValueResponse,
    summary="Retrieve decrypted secret value (Admin only)",
)
async def get_vault_secret(
    name: str,
    _: Annotated[Identity, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecretValueResponse:
    """Decrypt and return the stored secret value."""
    val = await resolve_secret(db, name)
    if val is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{name}' not found in vault.",
        )
    return SecretValueResponse(name=name, value=val)


@router.delete(
    "/secrets/{name}",
    status_code=status.HTTP_200_OK,
    summary="Delete a secret from the vault (Admin only)",
)
async def delete_vault_secret(
    name: str,
    _: Annotated[Identity, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str | bool]:
    """Remove a secret from the vault permanently."""
    deleted = await delete_secret(db, name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{name}' not found.",
        )
    return {"deleted": True, "name": name}
