"""Smoke test for the Varistha API health endpoint."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check() -> None:
    """Health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "varistha-api"


def test_root_endpoint() -> None:
    """Root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Varistha Control Plane API"
    assert "version" in data
