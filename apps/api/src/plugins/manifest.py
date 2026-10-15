"""Pydantic model representing a plugin manifest."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PluginManifest(BaseModel):
    """Declarative manifest describing a Varistha plugin."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Unique identifier of the plugin, e.g. web-fetch.")
    version: str = Field(default="0.1.0", description="Semver version string.")
    description: str = Field(default="", description="Human-readable description of capabilities.")
    transport: Literal["in-process", "mcp-stdio", "mcp-sse"] = Field(
        default="in-process",
        description="Transport mechanism for plugin execution.",
    )
    command: str | None = Field(default=None, description="CLI command for subprocess transports.")
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
    config_schema: str | None = Field(
        default=None,
        description="Relative path to configuration JSON Schema file.",
    )
