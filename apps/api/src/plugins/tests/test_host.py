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
