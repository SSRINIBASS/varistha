"""Integration tests for the Spec Diff API endpoints."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

BASE_SPEC: dict[str, Any] = {
    "apiVersion": "varistha/v1",
    "kind": "Agent",
    "metadata": {
        "name": "diff-agent",
        "owner": "lead@example.com",
        "stage": "prototype",
        "version": "0.1.0",
    },
    "spec": {
        "role": "Lead generation agent",
        "model": {"primary": "gpt-4o", "fallback": "ollama/llama3"},
        "instructions": "Initial instructions",
        "plugins": [
            {"name": "web-fetch", "enabled": True},
            {"name": "email-draft", "enabled": True},
        ],
        "autonomy": "L1",
        "guardrails": {
            "input": ["pii-redact"],
            "output": ["schema-valid"],
            "tools": ["rate-limit-50-per-day"],
        },
        "budget": {
            "max_usd_per_run": 0.50,
            "max_usd_per_day": 10.00,
        },
        "triggers": [{"type": "manual"}],
        "evals": {
            "suite": "./evals/suite.yaml",
            "min_pass_rate": 0.80,
        },
    },
}


@pytest.mark.asyncio
async def test_diff_published_versions_api(async_client: AsyncClient) -> None:
    """Compare two published versions and check structured diff results."""
    # Register v0.1.0
    v1_spec = copy.deepcopy(BASE_SPEC)
    reg_resp = await async_client.post("/api/v1/agents", json=v1_spec)
    assert reg_resp.status_code == 201

    # Publish v0.2.0 with breaking (autonomy L2, primary model swap) and non-breaking changes
    v2_spec = copy.deepcopy(BASE_SPEC)
    v2_spec["metadata"]["version"] = "0.2.0"
    v2_spec["spec"]["autonomy"] = "L2"  # Breaking: escalated
    v2_spec["spec"]["model"]["primary"] = "claude-3-5-sonnet"  # Breaking: primary model changed
    v2_spec["spec"]["budget"]["max_usd_per_day"] = 25.00  # Non-breaking: budget increased

    pub_resp = await async_client.post("/api/v1/agents/diff-agent/versions", json=v2_spec)
    assert pub_resp.status_code == 201

    # Diff v0.1.0 and v0.2.0
    diff_resp = await async_client.get("/api/v1/agents/diff-agent/versions/0.1.0/diff/0.2.0")
    assert diff_resp.status_code == 200

    data = diff_resp.json()
    assert data["from_version"] == "0.1.0"
    assert data["to_version"] == "0.2.0"
    assert data["has_changes"] is True
    assert data["has_breaking_changes"] is True
    assert data["summary"]["breaking"] >= 2
    assert len(data["breaking_entries"]) >= 2

    # Check fields in diff
    fields = [e["field"] for e in data["entries"]]
    assert "spec.autonomy" in fields
    assert "spec.model.primary" in fields
    assert "spec.budget.max_usd_per_day" in fields


@pytest.mark.asyncio
async def test_diff_versions_not_found(async_client: AsyncClient) -> None:
    """Return 404 when agent or version is missing."""
    # Unknown agent
    resp = await async_client.get("/api/v1/agents/unknown-slug/versions/0.1.0/diff/0.2.0")
    assert resp.status_code == 404

    # Known agent, unknown version
    spec = copy.deepcopy(BASE_SPEC)
    spec["metadata"]["name"] = "diff-agent-404"
    await async_client.post("/api/v1/agents", json=spec)

    resp2 = await async_client.get("/api/v1/agents/diff-agent-404/versions/0.1.0/diff/9.9.9")
    assert resp2.status_code == 404
    assert "not found" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_preview_spec_diff_api(async_client: AsyncClient) -> None:
    """Preview diff between an uncommitted candidate spec and the active version."""
    spec = copy.deepcopy(BASE_SPEC)
    spec["metadata"]["name"] = "preview-diff-agent"
    reg_resp = await async_client.post("/api/v1/agents", json=spec)
    assert reg_resp.status_code == 201

    # Candidate spec: remove guardrail 'pii-redact' (breaking), update instructions
    candidate = copy.deepcopy(spec)
    candidate["metadata"]["version"] = "0.2.0"
    candidate["spec"]["guardrails"]["input"] = []  # Breaking: guardrail removed
    candidate["spec"]["instructions"] = "New instructions for preview."

    resp = await async_client.post(
        "/api/v1/agents/preview-diff-agent/diff",
        json={"spec": candidate},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["has_changes"] is True
    assert data["has_breaking_changes"] is True
    assert any("pii-redact" in e["field"] for e in data["breaking_entries"])


@pytest.mark.asyncio
async def test_preview_spec_diff_invalid_spec(async_client: AsyncClient) -> None:
    """Preview diff with invalid candidate spec returns 422."""
    spec = copy.deepcopy(BASE_SPEC)
    spec["metadata"]["name"] = "invalid-preview-agent"
    await async_client.post("/api/v1/agents", json=spec)

    bad_candidate = copy.deepcopy(spec)
    bad_candidate["spec"]["autonomy"] = "INVALID_LEVEL"

    resp = await async_client.post(
        "/api/v1/agents/invalid-preview-agent/diff",
        json={"spec": bad_candidate},
    )
    assert resp.status_code == 422
    assert "validation failed" in resp.json()["detail"]["detail"].lower()


@pytest.mark.asyncio
async def test_preview_spec_diff_unknown_base_version(async_client: AsyncClient) -> None:
    """Preview diff against non-existent base version returns 404."""
    spec = copy.deepcopy(BASE_SPEC)
    spec["metadata"]["name"] = "base-ver-missing-agent"
    await async_client.post("/api/v1/agents", json=spec)

    candidate = copy.deepcopy(spec)
    candidate["metadata"]["version"] = "0.2.0"

    resp = await async_client.post(
        "/api/v1/agents/base-ver-missing-agent/diff",
        json={"spec": candidate, "base_version": "9.9.9"},
    )
    assert resp.status_code == 404
    assert "base version '9.9.9' not found" in resp.json()["detail"].lower()
