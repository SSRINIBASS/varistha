"""Unit and integration tests for Plugin Ecosystem API router."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from main import app
from plugins.host import PluginHost
from plugins.router import get_plugin_host

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def client() -> TestClient:
    """Test client for FastAPI app."""
    return TestClient(app)


def test_list_plugins_endpoint(client: TestClient) -> None:
    """GET /api/v1/plugins returns all discovered plugins with manifests."""
    response = client.get("/api/v1/plugins")
    assert response.status_code == 200
    data = response.json()

    assert "plugins" in data
    assert "total" in data
    assert data["total"] >= 1

    plugin_names = [p["name"] for p in data["plugins"]]
    assert "web-fetch" in plugin_names

    web_fetch = next(p for p in data["plugins"] if p["name"] == "web-fetch")
    assert web_fetch["version"] == "0.1.0"
    assert web_fetch["risk"] == "low"
    assert web_fetch["transport"] == "in-process"
    assert "network:read" in web_fetch["scopes"]
    assert web_fetch["untrusted_output"] is True
    assert "fetch_url" in web_fetch["tools"]
    assert web_fetch["config_schema"] is not None
    assert web_fetch["config_schema"]["type"] == "object"


def test_get_plugin_details_success(client: TestClient) -> None:
    """GET /api/v1/plugins/{name} returns plugin manifest details."""
    response = client.get("/api/v1/plugins/web-fetch")
    assert response.status_code == 200
    plugin = response.json()

    assert plugin["name"] == "web-fetch"
    assert plugin["risk"] == "low"
    assert plugin["requires_approval"] is False
    assert "fetch_url" in plugin["tools"]


def test_get_plugin_details_not_found(client: TestClient) -> None:
    """GET /api/v1/plugins/{name} returns 404 for uninstalled plugin."""
    response = client.get("/api/v1/plugins/non-existent-plugin-12345")
    assert response.status_code == 404
    error = response.json()
    assert "is not installed" in error["detail"]


def test_plugins_router_custom_host_dependency(tmp_path: Path) -> None:
    """Plugins router functions with a custom PluginHost instance."""
    plugin_dir = tmp_path / "custom-plugin"
    plugin_dir.mkdir()
    manifest_yaml = """
name: custom-plugin
version: 1.2.0
description: Custom test plugin
transport: in-process
risk: high
scopes:
  - storage:write
requires_approval: true
untrusted_output: false
"""
    (plugin_dir / "plugin.yaml").write_text(manifest_yaml, encoding="utf-8")

    custom_host = PluginHost(plugins_dir=tmp_path)
    app.dependency_overrides[get_plugin_host] = lambda: custom_host

    try:
        custom_client = TestClient(app)
        res = custom_client.get("/api/v1/plugins")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["plugins"][0]["name"] == "custom-plugin"
        assert data["plugins"][0]["risk"] == "high"
        assert data["plugins"][0]["requires_approval"] is True
    finally:
        app.dependency_overrides.pop(get_plugin_host, None)
