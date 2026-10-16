"""Tests for encrypted secrets vault service and REST API with RBAC."""

from __future__ import annotations

from typing import TYPE_CHECKING

from identity.models import Role
from identity.schemas import CreateApiKeyRequest, CreateSecretRequest
from identity.secrets_service import (
    delete_secret,
    list_secrets,
    resolve_secret,
    store_secret,
)
from identity.service import create_api_key
from shared.crypto import CIPHER_PREFIX
from shared.db.models.secrets import Secret
from sqlalchemy import select

if TYPE_CHECKING:
    import pytest
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_secrets_service_lifecycle(db_session: AsyncSession) -> None:
    """Secret service stores encrypted value at rest, resolves plaintext, and deletes."""
    req = CreateSecretRequest(
        name="hubspot_api_token",
        value="pat-na1-12345678-abcd-ef01-2345",
        description="HubSpot Integration Token",
    )

    # 1. Store secret
    stored = await store_secret(db_session, req)
    assert stored.name == "hubspot_api_token"
    assert stored.description == "HubSpot Integration Token"

    # Verify encrypted at rest in DB
    raw_stmt = select(Secret).where(Secret.name == "hubspot_api_token")
    raw_record = (await db_session.execute(raw_stmt)).scalar_one()
    assert raw_record.encrypted_value.startswith(CIPHER_PREFIX)
    assert "12345678" not in raw_record.encrypted_value
    assert raw_record.encrypted_value != req.value

    # 2. Resolve secret
    decrypted = await resolve_secret(db_session, "hubspot_api_token")
    assert decrypted == req.value

    # 3. Update secret
    update_req = CreateSecretRequest(
        name="hubspot_api_token",
        value="pat-na1-updated-token-9999",
        description="Updated token description",
    )
    updated = await store_secret(db_session, update_req)
    assert updated.description == "Updated token description"
    assert await resolve_secret(db_session, "hubspot_api_token") == "pat-na1-updated-token-9999"

    # 4. List secrets
    secrets_list = await list_secrets(db_session)
    assert len(secrets_list) == 1
    assert secrets_list[0].name == "hubspot_api_token"

    # 5. Delete secret
    deleted = await delete_secret(db_session, "hubspot_api_token")
    assert deleted is True
    assert await resolve_secret(db_session, "hubspot_api_token") is None

    # Deleting absent secret returns False
    assert await delete_secret(db_session, "hubspot_api_token") is False


async def test_secrets_api_rbac_enforcement(
    async_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Secrets API enforces strict role hierarchy across admin, operator, and viewer."""
    # Enable auth
    import shared.config

    settings = shared.config.get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)

    # Issue API keys
    _, admin_key = await create_api_key(
        db_session, CreateApiKeyRequest(name="admin-client", role=Role.ADMIN)
    )
    _, operator_key = await create_api_key(
        db_session, CreateApiKeyRequest(name="op-client", role=Role.OPERATOR)
    )
    _, viewer_key = await create_api_key(
        db_session, CreateApiKeyRequest(name="view-client", role=Role.VIEWER)
    )

    admin_headers = {"X-API-Key": admin_key}
    operator_headers = {"X-API-Key": operator_key}
    viewer_headers = {"X-API-Key": viewer_key}

    secret_payload = {
        "name": "resend_api_key",
        "value": "re_123456789_abcdefg",
        "description": "Production Resend API Key",
    }

    # 1. Viewer cannot create secret
    resp = await async_client.post(
        "/api/v1/auth/secrets", json=secret_payload, headers=viewer_headers
    )
    assert resp.status_code == 403

    # 2. Operator cannot create secret (Admin only)
    resp = await async_client.post(
        "/api/v1/auth/secrets", json=secret_payload, headers=operator_headers
    )
    assert resp.status_code == 403

    # 3. Admin creates secret
    resp = await async_client.post(
        "/api/v1/auth/secrets", json=secret_payload, headers=admin_headers
    )
    assert resp.status_code == 201
    created_data = resp.json()
    assert created_data["name"] == "resend_api_key"
    assert created_data["description"] == "Production Resend API Key"
    assert "value" not in created_data  # Plaintext value omitted from metadata!

    # 4. Viewer cannot list secrets
    resp = await async_client.get("/api/v1/auth/secrets", headers=viewer_headers)
    assert resp.status_code == 403

    # 5. Operator can list secrets
    resp = await async_client.get("/api/v1/auth/secrets", headers=operator_headers)
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 1
    assert listed[0]["name"] == "resend_api_key"
    assert "value" not in listed[0]

    # 6. Operator cannot read decrypted secret value (Admin only)
    resp = await async_client.get("/api/v1/auth/secrets/resend_api_key", headers=operator_headers)
    assert resp.status_code == 403

    # 7. Admin reads decrypted secret value
    resp = await async_client.get("/api/v1/auth/secrets/resend_api_key", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["value"] == "re_123456789_abcdefg"

    # 8. Operator cannot delete secret
    resp = await async_client.delete(
        "/api/v1/auth/secrets/resend_api_key", headers=operator_headers
    )
    assert resp.status_code == 403

    # 9. Admin deletes secret
    resp = await async_client.delete("/api/v1/auth/secrets/resend_api_key", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    # 10. Subsequent read returns 404
    resp = await async_client.get("/api/v1/auth/secrets/resend_api_key", headers=admin_headers)
    assert resp.status_code == 404
