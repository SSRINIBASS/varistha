"""Unit tests for the PluginHost and permission enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from plugins.host import PluginHost, PluginNotFoundError, PluginPermissionError

if TYPE_CHECKING:
    from pathlib import Path


def test_discover_plugins_finds_web_fetch() -> None:
    """PluginHost scans the plugins directory and registers web-fetch."""
    host = PluginHost()
    manifests = host.discover_plugins()

    assert "web-fetch" in manifests
    manifest = host.get_manifest("web-fetch")
    assert manifest.name == "web-fetch"
    assert manifest.version == "0.1.0"
    assert manifest.risk == "low"
    assert "network:read" in manifest.scopes
    assert manifest.untrusted_output is True


def test_get_manifest_unknown_plugin_raises() -> None:
    """Requesting an uninstalled plugin raises PluginNotFoundError."""
    host = PluginHost()
    with pytest.raises(PluginNotFoundError):
        host.get_manifest("non-existent-plugin")


def test_is_plugin_enabled_evaluation() -> None:
    """Permission checker correctly evaluates agent spec plugin list."""
    host = PluginHost()

    spec_enabled = {
        "spec": {
            "plugins": [
                {"name": "web-fetch", "enabled": True},
                {"name": "email-send", "enabled": False},
            ],
        },
    }

    assert host.is_plugin_enabled("web-fetch", spec_enabled) is True
    assert host.is_plugin_enabled("email-send", spec_enabled) is False
    assert host.is_plugin_enabled("linkedin-post", spec_enabled) is False


@pytest.mark.asyncio
async def test_execute_tool_permission_denied_when_disabled() -> None:
    """PluginHost raises PluginPermissionError if plugin is disabled in agent spec."""
    host = PluginHost()

    spec_disabled = {
        "spec": {
            "plugins": [{"name": "web-fetch", "enabled": False}],
        },
    }

    with pytest.raises(PluginPermissionError) as exc_info:
        await host.execute_tool(
            plugin_name="web-fetch",
            tool_name="fetch_url",
            args={"url": "https://example.com"},
            agent_spec=spec_disabled,
        )

    assert "Permission denied" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_tool_success_marks_untrusted() -> None:
    """Executing an enabled tool returns structured output with untrusted=True."""
    host = PluginHost()

    mock_handler = AsyncMock(
        return_value={"url": "https://example.com", "content": "Extracted text"}
    )
    host.register_handler("web-fetch", "test_tool", mock_handler)

    spec_enabled = {
        "spec": {
            "plugins": [{"name": "web-fetch", "enabled": True}],
        },
    }

    result = await host.execute_tool(
        plugin_name="web-fetch",
        tool_name="test_tool",
        args={"url": "https://example.com"},
        agent_spec=spec_enabled,
    )

    assert result["content"] == "Extracted text"
    assert result["untrusted"] is True
    mock_handler.assert_awaited_once_with(url="https://example.com")


def test_get_tool_definitions_formats_openai_schema() -> None:
    """PluginHost generates valid LLM tool calling schema."""
    host = PluginHost()
    tools = host.get_tool_definitions(enabled_plugin_names=["web-fetch"])

    assert len(tools) == 1
    tool = tools[0]
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "web_fetch"
    assert "url" in tool["function"]["parameters"]["properties"]
    assert "url" in tool["function"]["parameters"]["required"]


def test_custom_empty_plugins_dir(tmp_path: Path) -> None:
    """PluginHost handles non-existent or empty directory gracefully."""
    empty_host = PluginHost(plugins_dir=tmp_path / "non_existent")
    assert empty_host.discover_plugins() == {}


@pytest.mark.asyncio
async def test_execute_tool_missing_handler_raises() -> None:
    """PluginHost raises PluginNotFoundError when tool name is not registered."""
    host = PluginHost()
    spec = {"spec": {"plugins": [{"name": "web-fetch", "enabled": True}]}}

    with pytest.raises(PluginNotFoundError) as exc_info:
        await host.execute_tool(
            plugin_name="web-fetch",
            tool_name="unregistered_tool",
            args={},
            agent_spec=spec,
        )

    assert "unregistered_tool" in str(exc_info.value)


def test_discover_plugins_finds_all_core_plugins() -> None:
    """PluginHost scans the plugins directory and registers all core plugins."""
    host = PluginHost()
    manifests = host.discover_plugins()

    assert "web-fetch" in manifests
    assert "web-search" in manifests
    assert "web-scrape" in manifests
    assert "crm-export" in manifests

    search_manifest = host.get_manifest("web-search")
    assert search_manifest.risk == "low"
    assert search_manifest.untrusted_output is True

    scrape_manifest = host.get_manifest("web-scrape")
    assert scrape_manifest.risk == "low"
    assert scrape_manifest.untrusted_output is True

    crm_manifest = host.get_manifest("crm-export")
    assert crm_manifest.risk == "medium"
    assert crm_manifest.untrusted_output is False


def test_get_tool_definitions_all_core_plugins() -> None:
    """PluginHost generates valid LLM tool definitions for all core research plugins."""
    host = PluginHost()
    tools = host.get_tool_definitions(
        enabled_plugin_names=["web-fetch", "web-search", "web-scrape", "crm-export"]
    )

    names = [t["function"]["name"] for t in tools]
    assert "web_fetch" in names
    assert "web_search" in names
    assert "web_scrape" in names
    assert "crm_export" in names


@pytest.mark.asyncio
async def test_execute_core_tools_integration() -> None:
    """PluginHost executes web-search and crm-export with proper trust boundary flags."""
    host = PluginHost()
    spec = {
        "spec": {
            "plugins": [
                {"name": "web-search", "enabled": True},
                {"name": "crm-export", "enabled": True},
            ],
        },
    }

    # Execute web_search in mock mode
    search_res = await host.execute_tool(
        plugin_name="web-search",
        tool_name="web_search",
        args={"query": "AI employee control plane", "engine": "mock", "max_results": 2},
        agent_spec=spec,
    )
    assert search_res["total_results"] == 2
    assert search_res["untrusted"] is True

    # Execute crm_export
    crm_res = await host.execute_tool(
        plugin_name="crm-export",
        tool_name="crm_export",
        args={"leads": [{"email": "founder@acme.com", "company": "Acme AI"}], "format": "csv"},
        agent_spec=spec,
    )
    assert crm_res["format"] == "csv"
    assert "founder@acme.com" in crm_res["payload"]
    assert "untrusted" not in crm_res  # untrusted_output: false
