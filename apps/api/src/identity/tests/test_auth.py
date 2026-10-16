"""Unit and integration tests for Identity and RBAC authentication."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from identity.models import Identity, Role
from identity.schemas import CreateApiKeyRequest
from identity.service import (
    authenticate_api_key,
    create_api_key,
    generate_key_material,
    hash_key,
    revoke_api_key,
)
from shared.config import get_settings

if TYPE_CHECKING:
    import pytest
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


def test_generate_key_material() -> None:
    """generate_key_material produces standard prefix and valid sha256 hash."""
    raw_key, prefix, key_hash = generate_key_material()

    assert raw_key.startswith("var_live_")
    assert len(raw_key) > 30
    assert prefix == raw_key[:14]
    assert key_hash == hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    assert hash_key(raw_key) == key_hash


def test_role_hierarchy_evaluation() -> None:
    """Role hierarchy accurately gates minimum permissions."""
    import uuid

    admin = Identity(id=uuid.uuid4(), name="Admin", role=Role.ADMIN)
    operator = Identity(id=uuid.uuid4(), name="Operator", role=Role.OPERATOR)
    viewer = Identity(id=uuid.uuid4(), name="Viewer", role=Role.VIEWER)

    # Admin satisfies all
    assert admin.has_role(Role.ADMIN) is True
    assert admin.has_role(Role.OPERATOR) is True
    assert admin.has_role(Role.VIEWER) is True

    # Operator satisfies Operator and Viewer, not Admin
    assert operator.has_role(Role.ADMIN) is False
    assert operator.has_role(Role.OPERATOR) is True
    assert operator.has_role(Role.VIEWER) is True

    # Viewer only satisfies Viewer
    assert viewer.has_role(Role.ADMIN) is False
    assert viewer.has_role(Role.OPERATOR) is False
    assert viewer.has_role(Role.VIEWER) is True


async def test_api_key_service_lifecycle(db_session: AsyncSession) -> None:
    """Service creates, authenticates, and revokes API keys cleanly."""
    req = CreateApiKeyRequest(name="Test Key", role=Role.OPERATOR, expires_in_days=30)
    key_record, raw_key = await create_api_key(db_session, req)

    assert key_record.name == "Test Key"
    assert key_record.role == "operator"
    assert key_record.is_active is True
    assert key_record.last_used_at is None

    # Successful authentication
    authenticated = await authenticate_api_key(db_session, raw_key)
    assert authenticated is not None
    assert authenticated.id == key_record.id
    assert authenticated.last_used_at is not None

    # Invalid token fails authentication
    assert await authenticate_api_key(db_session, "var_live_invalidtoken") is None

    # Revoke key
    revoked = await revoke_api_key(db_session, key_record.id)
    assert revoked is True
    assert key_record.is_active is False

    # Revoked key fails authentication
    assert await authenticate_api_key(db_session, raw_key) is None


async def test_auth_endpoints_rbac_lifecycle(async_client: AsyncClient) -> None:
    """API endpoints enforce role-based access control and token authentication."""
    # 1. In dev mode (auth_enabled=False), caller defaults to dev-admin
    me_resp = await async_client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "admin"

    # 2. Admin creates an Operator key
    create_op_resp = await async_client.post(
        "/api/v1/auth/keys",
        json={"name": "Operator Bot", "role": "operator"},
    )
    assert create_op_resp.status_code == 201
    op_data = create_op_resp.json()
    op_key = op_data["raw_key"]
    op_id = op_data["id"]

    # 3. Caller with Operator key verifies identity
    op_me = await async_client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": op_key},
    )
    assert op_me.status_code == 200
    assert op_me.json()["role"] == "operator"

    # 4. Operator is forbidden from creating new keys (Admin only)
    forbidden_resp = await async_client.post(
        "/api/v1/auth/keys",
        json={"name": "Sub Key", "role": "viewer"},
        headers={"X-API-Key": op_key},
    )
    assert forbidden_resp.status_code == 403

    # 5. Admin creates a Viewer key
    create_vw_resp = await async_client.post(
        "/api/v1/auth/keys",
        json={"name": "Dashboard Viewer", "role": "viewer"},
    )
    assert create_vw_resp.status_code == 201
    vw_key = create_vw_resp.json()["raw_key"]

    # 6. Viewer can authenticate via Authorization Bearer header
    vw_me = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {vw_key}"},
    )
    assert vw_me.status_code == 200
    assert vw_me.json()["role"] == "viewer"

    # 7. Admin lists all keys
    list_resp = await async_client.get("/api/v1/auth/keys")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 2

    # 8. Admin revokes the operator key
    del_resp = await async_client.delete(f"/api/v1/auth/keys/{op_id}")
    assert del_resp.status_code == 200

    # 9. Revoked key returns 401 Unauthorized
    revoked_me = await async_client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": op_key},
    )
    assert revoked_me.status_code == 401


async def test_auth_enabled_strict_enforcement(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When auth_enabled is true, missing API key returns 401."""
    # First create a valid key while in dev mode
    create_resp = await async_client.post(
        "/api/v1/auth/keys",
        json={"name": "Prod Admin", "role": "admin"},
    )
    assert create_resp.status_code == 201
    valid_key = create_resp.json()["raw_key"]

    # Enable strict auth
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)

    # Request without key fails with 401
    unauth_resp = await async_client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401
    assert "API key required" in unauth_resp.json()["detail"]

    # Request with valid key succeeds
    auth_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": valid_key},
    )
    assert auth_resp.status_code == 200
    assert auth_resp.json()["role"] == "admin"
