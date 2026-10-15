"""Pydantic schemas for Plugin Ecosystem API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PluginInfoResponse(BaseModel):
    """Structured information about an installed plugin."""

    name: str = Field(description="Unique identifier of the plugin, e.g. web-fetch.")
    version: str = Field(default="0.1.0", description="Semver version string.")
    description: str = Field(default="", description="Human-readable description of capabilities.")
    transport: Literal["in-process", "mcp-stdio", "mcp-sse"] = Field(
        default="in-process",
        description="Transport mechanism for plugin execution.",
    )
    risk: Literal["low", "medium", "high"] = Field(
        default="low",
        description="Risk assessment level governing default autonomy requirements.",
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="Permission scopes required by the plugin (e.g. network:read).",
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether tool invocations require human approval before execution.",
    )
    untrusted_output: bool = Field(
        default=True,
        description="Whether data returned by this plugin must be treated as untrusted.",
    )
    config_schema: dict[str, Any] | None = Field(
        default=None,
        description="Parsed JSON schema for plugin configuration if provided.",
    )
    tools: list[str] = Field(
        default_factory=list,
        description="List of tool handler names registered for this plugin.",
    )


class PluginListResponse(BaseModel):
    """Response containing list of all discovered plugins."""

    plugins: list[PluginInfoResponse]
    total: int
