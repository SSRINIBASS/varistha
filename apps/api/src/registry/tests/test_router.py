"""Integration tests for the Agent Registry API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from httpx import AsyncClient


def _make_spec(
    name: str = "lead-researcher",
    version: str = "0.1.0",
    stage: str = "prototype",
    owner: str = "founder@example.com",
) -> dict[str, Any]:
    """Return a valid raw AgentSpec dict."""
    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": owner,
            "stage": stage,
            "version": version,
        },
        "spec": {
            "role": f"Test role for {name}",
            "model": {"primary": "gpt-4o"},
            "instructions": "Test instructions",
            "autonomy": "L1",
            "triggers": [{"type": "manual"}],
        },
    }


async def test_register_agent_success(async_client: AsyncClient) -> None:
    """POST /api/v1/agents with a valid spec registers an agent and initial version."""
    spec = _make_spec(name="researcher-one", version="1.0.0")

    response = await async_client.post("/api/v1/agents", json=spec)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "researcher-one"
    assert data["stage"] == "prototype"
    assert data["current_version"] == "1.0.0"
    assert data["version_count"] == 1
    assert data["latest_spec"]["metadata"]["name"] == "researcher-one"
    assert "id" in data


async def test_register_agent_spec_validation_failure(async_client: AsyncClient) -> None:
    """POST /api/v1/agents with invalid spec returns 422 with structured error list."""
    spec = _make_spec(name="Bad Name With Spaces")

    response = await async_client.post("/api/v1/agents", json=spec)

    assert response.status_code == 422
    data = response.json()
    assert "errors" in data["detail"]
    assert any("metadata -> name" in err for err in data["detail"]["errors"])


async def test_register_duplicate_version_conflict(async_client: AsyncClient) -> None:
    """Registering the same version twice returns 409 Conflict."""
    spec = _make_spec(name="unique-agent", version="0.1.0")

    resp1 = await async_client.post("/api/v1/agents", json=spec)
    assert resp1.status_code == 201

    resp2 = await async_client.post("/api/v1/agents", json=spec)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


async def test_list_agents_and_filtering(async_client: AsyncClient) -> None:
    """GET /api/v1/agents lists agents and supports stage & owner query filters."""
    spec1 = _make_spec(name="agent-a", stage="prototype", owner="alpha@example.com")
    spec2 = _make_spec(name="agent-b", stage="staging", owner="beta@example.com")

    await async_client.post("/api/v1/agents", json=spec1)
    await async_client.post("/api/v1/agents", json=spec2)

    # List all
    all_resp = await async_client.get("/api/v1/agents")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert all_data["total"] == 2
    assert len(all_data["items"]) == 2

    # Filter by stage
    staging_resp = await async_client.get("/api/v1/agents?stage=staging")
    assert staging_resp.status_code == 200
    staging_data = staging_resp.json()
    assert staging_data["total"] == 1
    assert staging_data["items"][0]["name"] == "agent-b"

    # Filter by owner
    owner_resp = await async_client.get("/api/v1/agents?owner=alpha@example.com")
    assert owner_resp.status_code == 200
    owner_data = owner_resp.json()
    assert owner_data["total"] == 1
    assert owner_data["items"][0]["name"] == "agent-a"


async def test_get_agent_by_slug_and_uuid(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{id_or_name} resolves by both slug name and UUID."""
    spec = _make_spec(name="lookup-agent", version="0.5.0")
    create_resp = await async_client.post("/api/v1/agents", json=spec)
    agent_id = create_resp.json()["id"]

    # Lookup by name
    name_resp = await async_client.get("/api/v1/agents/lookup-agent")
    assert name_resp.status_code == 200
    assert name_resp.json()["id"] == agent_id

    # Lookup by UUID
    uuid_resp = await async_client.get(f"/api/v1/agents/{agent_id}")
    assert uuid_resp.status_code == 200
    assert uuid_resp.json()["name"] == "lookup-agent"


async def test_get_agent_not_found(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{id_or_name} returns 404 for unknown agent."""
    response = await async_client.get("/api/v1/agents/non-existent-agent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_get_agent_versions(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{id_or_name}/versions lists historical snapshots."""
    v1_spec = _make_spec(name="multi-ver", version="1.0.0")
    v2_spec = _make_spec(name="multi-ver", version="1.1.0")

    await async_client.post("/api/v1/agents", json=v1_spec)
    await async_client.post("/api/v1/agents", json=v2_spec)

    resp = await async_client.get("/api/v1/agents/multi-ver/versions")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2
    version_strings = [v["version"] for v in versions]
    assert version_strings == ["1.1.0", "1.0.0"]


async def test_get_agent_version_detail(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{id_or_name}/versions/{version} returns exact spec snapshot."""
    spec = _make_spec(name="detail-agent", version="2.0.0")
    await async_client.post("/api/v1/agents", json=spec)

    resp = await async_client.get("/api/v1/agents/detail-agent/versions/2.0.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "2.0.0"
    assert data["spec"]["metadata"]["name"] == "detail-agent"


async def test_get_agent_version_not_found(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{id_or_name}/versions/{version} returns 404 for missing version."""
    spec = _make_spec(name="v-agent", version="1.0.0")
    await async_client.post("/api/v1/agents", json=spec)

    resp = await async_client.get("/api/v1/agents/v-agent/versions/9.9.9")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


async def test_publish_new_version_endpoint(async_client: AsyncClient) -> None:
    """POST /api/v1/agents/{id_or_name}/versions publishes a new version."""
    v1_spec = _make_spec(name="pub-agent", version="0.1.0")
    await async_client.post("/api/v1/agents", json=v1_spec)

    v2_spec = _make_spec(name="pub-agent", version="0.2.0")
    resp = await async_client.post("/api/v1/agents/pub-agent/versions", json=v2_spec)

    assert resp.status_code == 201
    assert resp.json()["version"] == "0.2.0"

    # Agent current_version updated
    agent_resp = await async_client.get("/api/v1/agents/pub-agent")
    assert agent_resp.json()["current_version"] == "0.2.0"
    assert agent_resp.json()["version_count"] == 2


async def test_publish_version_mismatched_name_error(async_client: AsyncClient) -> None:
    """POST /api/v1/agents/{id_or_name}/versions rejects spec with mismatched name."""
    v1_spec = _make_spec(name="target-agent", version="0.1.0")
    await async_client.post("/api/v1/agents", json=v1_spec)

    mismatched = _make_spec(name="other-agent", version="0.2.0")
    resp = await async_client.post("/api/v1/agents/target-agent/versions", json=mismatched)

    assert resp.status_code == 400
    assert "does not match target agent" in resp.json()["detail"]


async def test_subresource_nonexistent_agent_returns_404(async_client: AsyncClient) -> None:
    """Subresource routes return 404 when target agent does not exist."""
    resp_list = await async_client.get("/api/v1/agents/ghost/versions")
    assert resp_list.status_code == 404

    resp_detail = await async_client.get("/api/v1/agents/ghost/versions/1.0.0")
    assert resp_detail.status_code == 404

    spec = _make_spec(name="ghost", version="1.0.0")
    resp_pub = await async_client.post("/api/v1/agents/ghost/versions", json=spec)
    assert resp_pub.status_code == 404


async def test_publish_version_invalid_and_duplicate(async_client: AsyncClient) -> None:
    """POST /api/v1/agents/{id}/versions validates specs and rejects duplicates."""
    spec = _make_spec(name="pub-edge", version="1.0.0")
    await async_client.post("/api/v1/agents", json=spec)

    # Publish invalid spec (bad semver)
    invalid_spec = _make_spec(name="pub-edge", version="not-a-semver")
    resp_inv = await async_client.post("/api/v1/agents/pub-edge/versions", json=invalid_spec)
    assert resp_inv.status_code == 422

    # Publish duplicate version
    resp_dup = await async_client.post("/api/v1/agents/pub-edge/versions", json=spec)
    assert resp_dup.status_code == 409
    assert "already exists" in resp_dup.json()["detail"]
