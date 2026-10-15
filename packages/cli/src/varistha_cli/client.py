"""HTTP client for communicating with the Varistha control plane API."""

from __future__ import annotations

from typing import Any

import httpx


class VaristhaClientError(Exception):
    """Base exception for CLI API client errors."""


class VaristhaConnectionError(VaristhaClientError):
    """Raised when connection to Varistha API fails."""


class VaristhaApiError(VaristhaClientError):
    """Raised when Varistha API returns an error response."""

    def __init__(self, status_code: int, message: str, details: Any = None) -> None:
        """Initialize with status code and details."""
        super().__init__(f"API Error ({status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.details = details


def _safe_details(resp: httpx.Response) -> Any:
    """Safely extract JSON or raw text details from HTTP response."""
    if not resp.text:
        return None
    try:
        return resp.json()
    except Exception:
        return resp.text


class VaristhaClient:
    """Client for Varistha REST API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0) -> None:
        """Initialize client with base URL."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def client(self) -> httpx.Client:
        """Create an HTTPX sync client."""
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def check_health(self) -> bool:
        """Check if API server is reachable and healthy."""
        try:
            with self.client() as http_client:
                resp = http_client.get("/health")
                return resp.status_code == 200
        except Exception:
            return False

    def get_agent(self, id_or_name: str) -> dict[str, Any] | None:
        """Get agent by UUID or name slug. Returns None if 404."""
        try:
            with self.client() as http_client:
                resp = http_client.get(f"/api/v1/agents/{id_or_name}")
                if resp.status_code == 404:
                    return None
                if resp.status_code != 200:
                    raise VaristhaApiError(resp.status_code, resp.text, details=_safe_details(resp))
                data: dict[str, Any] = resp.json()
                return data
        except httpx.ConnectError as err:
            raise VaristhaConnectionError(
                f"Could not connect to Varistha API at {self.base_url}. Is the server running?"
            ) from err
        except httpx.RequestError as err:
            raise VaristhaConnectionError(f"Request to {self.base_url} failed: {err}") from err

    def create_agent(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Register a new agent in the registry."""
        try:
            with self.client() as http_client:
                resp = http_client.post("/api/v1/agents", json=spec)
                if resp.status_code not in (200, 201):
                    raise VaristhaApiError(
                        resp.status_code,
                        f"Failed to create agent: {resp.text}",
                        details=_safe_details(resp),
                    )
                data: dict[str, Any] = resp.json()
                return data
        except httpx.ConnectError as err:
            raise VaristhaConnectionError(
                f"Could not connect to Varistha API at {self.base_url}. Is the server running?"
            ) from err
        except httpx.RequestError as err:
            raise VaristhaConnectionError(f"Request to {self.base_url} failed: {err}") from err

    def create_agent_version(self, id_or_name: str, spec: dict[str, Any]) -> dict[str, Any]:
        """Create a new version for an existing agent."""
        try:
            with self.client() as http_client:
                resp = http_client.post(f"/api/v1/agents/{id_or_name}/versions", json=spec)
                if resp.status_code not in (200, 201):
                    raise VaristhaApiError(
                        resp.status_code,
                        f"Failed to create agent version: {resp.text}",
                        details=_safe_details(resp),
                    )
                data: dict[str, Any] = resp.json()
                return data
        except httpx.ConnectError as err:
            raise VaristhaConnectionError(
                f"Could not connect to Varistha API at {self.base_url}. Is the server running?"
            ) from err
        except httpx.RequestError as err:
            raise VaristhaConnectionError(f"Request to {self.base_url} failed: {err}") from err

    def trigger_run(
        self,
        id_or_name: str,
        input_data: dict[str, Any] | None = None,
        trigger_type: str = "manual",
    ) -> dict[str, Any]:
        """Trigger an execution run for an agent."""
        payload: dict[str, Any] = {
            "trigger_type": trigger_type,
            "input": input_data or {},
        }
        try:
            with self.client() as http_client:
                resp = http_client.post(f"/api/v1/agents/{id_or_name}/runs", json=payload)
                if resp.status_code not in (200, 201):
                    raise VaristhaApiError(
                        resp.status_code,
                        f"Failed to trigger run: {resp.text}",
                        details=_safe_details(resp),
                    )
                data: dict[str, Any] = resp.json()
                return data
        except httpx.ConnectError as err:
            raise VaristhaConnectionError(
                f"Could not connect to Varistha API at {self.base_url}. Is the server running?"
            ) from err
        except httpx.RequestError as err:
            raise VaristhaConnectionError(f"Request to {self.base_url} failed: {err}") from err

    def get_run(self, run_id: str) -> dict[str, Any]:
        """Get run status and execution details by UUID."""
        try:
            with self.client() as http_client:
                resp = http_client.get(f"/api/v1/runs/{run_id}")
                if resp.status_code != 200:
                    raise VaristhaApiError(
                        resp.status_code,
                        f"Failed to get run {run_id}: {resp.text}",
                        details=_safe_details(resp),
                    )
                data: dict[str, Any] = resp.json()
                return data
        except httpx.ConnectError as err:
            raise VaristhaConnectionError(
                f"Could not connect to Varistha API at {self.base_url}. Is the server running?"
            ) from err
        except httpx.RequestError as err:
            raise VaristhaConnectionError(f"Request to {self.base_url} failed: {err}") from err
