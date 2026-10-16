"""Request and response schemas for identity and API keys."""

from __future__ import annotations

import uuid
from datetime import datetime

from identity.models import Role
from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    """Payload to generate a new API key."""

    name: str = Field(
        ..., min_length=2, max_length=100, description="Descriptive label for the key"
    )
    role: Role = Field(default=Role.OPERATOR, description="Authorization role granted to this key")
    expires_in_days: int | None = Field(
        default=None, ge=1, le=365, description="Optional lifetime in days"
    )


class ApiKeyResponse(BaseModel):
    """Public details of an existing API key."""

    id: uuid.UUID
    name: str
    prefix: str
    role: Role
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool


class CreatedApiKeyResponse(ApiKeyResponse):
    """Response returned upon creation, containing the plaintext key once."""

    raw_key: str = Field(
        ..., description="Plaintext secret key. Only displayed once upon creation."
    )


class CurrentIdentityResponse(BaseModel):
    """Caller identity information."""

    id: uuid.UUID
    name: str
    role: Role
    api_key_id: uuid.UUID | None = None


class CreateSecretRequest(BaseModel):
    """Payload to store or update a secret in the encrypted vault."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        description="Unique identifier name for the secret",
    )
    value: str = Field(..., min_length=1, description="Secret plaintext value to encrypt at rest")
    description: str | None = Field(default=None, max_length=256)


class SecretMetadataResponse(BaseModel):
    """Metadata of a stored secret, omitting the secret value."""

    id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class SecretValueResponse(BaseModel):
    """Decrypted secret value."""

    name: str
    value: str
