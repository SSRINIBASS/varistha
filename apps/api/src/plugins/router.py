"""FastAPI router for Plugin Ecosystem and Capability Registry."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from plugins.host import PluginHost, PluginNotFoundError
from plugins.schemas import PluginInfoResponse, PluginListResponse

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])

# Shared PluginHost instance
_plugin_host: PluginHost | None = None


def get_plugin_host() -> PluginHost:
    """Retrieve or initialize the shared PluginHost instance."""
    global _plugin_host
    if _plugin_host is None:
        _plugin_host = PluginHost()
    return _plugin_host


@router.get("", response_model=PluginListResponse)
def list_plugins(
    host: Annotated[PluginHost, Depends(get_plugin_host)],
) -> PluginListResponse:
    """List all installed and discovered plugins with their manifests."""
    manifests = host.discover_plugins()
    plugin_items: list[PluginInfoResponse] = []

    for name, manifest in sorted(manifests.items()):
        plugin_items.append(
            PluginInfoResponse(
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                transport=manifest.transport,
                risk=manifest.risk,
                scopes=manifest.scopes,
                requires_approval=manifest.requires_approval,
                untrusted_output=manifest.untrusted_output,
                config_schema=host.get_config_schema(name),
                tools=host.get_tools_for_plugin(name),
            )
        )

    return PluginListResponse(plugins=plugin_items, total=len(plugin_items))


@router.get("/{name}", response_model=PluginInfoResponse)
def get_plugin(
    name: str,
    host: Annotated[PluginHost, Depends(get_plugin_host)],
) -> PluginInfoResponse:
    """Retrieve detailed manifest and configuration schema for a specific plugin."""
    try:
        manifest = host.get_manifest(name)
        return PluginInfoResponse(
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            transport=manifest.transport,
            risk=manifest.risk,
            scopes=manifest.scopes,
            requires_approval=manifest.requires_approval,
            untrusted_output=manifest.untrusted_output,
            config_schema=host.get_config_schema(name),
            tools=host.get_tools_for_plugin(name),
        )
    except PluginNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' is not installed.",
        ) from err
