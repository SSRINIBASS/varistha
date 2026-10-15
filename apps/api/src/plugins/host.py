"""Plugin host responsible for discovery, manifest validation, and tool execution."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from plugins.manifest import PluginManifest
from pydantic import ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable


class PluginNotFoundError(Exception):
    """Raised when a requested plugin is not installed."""


class PluginPermissionError(Exception):
    """Raised when an agent attempts to execute a tool from an unapproved plugin."""


class PluginHost:
    """Manages discovery and safe execution of plugins outside the language model."""

    def __init__(self, plugins_dir: Path | None = None) -> None:
        """Initialize plugin host with path to plugins directory."""
        if plugins_dir is None:
            # Default to repo root / plugins
            repo_root = Path(__file__).resolve().parents[4]
            self.plugins_dir = repo_root / "plugins"
        else:
            self.plugins_dir = plugins_dir

        self._manifests: dict[str, PluginManifest] = {}
        self._tool_handlers: dict[str, dict[str, Callable[..., Any]]] = {}
        self.discover_plugins()
        self._register_built_in_handlers()

    def discover_plugins(self) -> dict[str, PluginManifest]:
        """Scan the plugins directory for valid plugin.yaml manifests."""
        self._manifests.clear()

        if not self.plugins_dir.exists() or not self.plugins_dir.is_dir():
            return self._manifests

        for child in self.plugins_dir.iterdir():
            if child.is_dir():
                manifest_file = child / "plugin.yaml"
                if manifest_file.exists():
                    try:
                        content = yaml.safe_load(manifest_file.read_text(encoding="utf-8"))
                        if isinstance(content, dict):
                            manifest = PluginManifest.model_validate(content)
                            self._manifests[manifest.name] = manifest
                    except (yaml.YAMLError, ValueError, ValidationError):
                        continue

        return self._manifests

    def get_manifest(self, plugin_name: str) -> PluginManifest:
        """Retrieve manifest for a given plugin name."""
        if plugin_name not in self._manifests:
            raise PluginNotFoundError(f"Plugin '{plugin_name}' is not registered.")
        return self._manifests[plugin_name]

    def _register_built_in_handlers(self) -> None:
        """Register execution handlers for in-process plugins."""
        # 1. web-fetch
        web_fetch_dir = self.plugins_dir / "web-fetch"
        if web_fetch_dir.exists() and str(web_fetch_dir) not in sys.path:
            sys.path.insert(0, str(web_fetch_dir))
        try:
            from fetcher import fetch_url  # pyright: ignore[reportMissingImports]

            self.register_handler("web-fetch", "fetch_url", fetch_url)
            self.register_handler("web-fetch", "web_fetch", fetch_url)
        except ImportError:
            pass

        # 2. web-search
        web_search_dir = self.plugins_dir / "web-search"
        if web_search_dir.exists() and str(web_search_dir) not in sys.path:
            sys.path.insert(0, str(web_search_dir))
        try:
            from searcher import search_web  # pyright: ignore[reportMissingImports]

            self.register_handler("web-search", "search_web", search_web)
            self.register_handler("web-search", "web_search", search_web)
        except ImportError:
            pass

        # 3. web-scrape
        web_scrape_dir = self.plugins_dir / "web-scrape"
        if web_scrape_dir.exists() and str(web_scrape_dir) not in sys.path:
            sys.path.insert(0, str(web_scrape_dir))
        try:
            from scraper import scrape_url  # pyright: ignore[reportMissingImports]

            self.register_handler("web-scrape", "scrape_url", scrape_url)
            self.register_handler("web-scrape", "web_scrape", scrape_url)
        except ImportError:
            pass

        # 4. crm-export
        crm_export_dir = self.plugins_dir / "crm-export"
        if crm_export_dir.exists() and str(crm_export_dir) not in sys.path:
            sys.path.insert(0, str(crm_export_dir))
        try:
            from exporter import export_leads  # pyright: ignore[reportMissingImports]

            self.register_handler("crm-export", "export_leads", export_leads)
            self.register_handler("crm-export", "crm_export", export_leads)
        except ImportError:
            pass

    def register_handler(
        self,
        plugin_name: str,
        tool_name: str,
        handler: Callable[..., Any],
    ) -> None:
        """Register an executable callable for a plugin tool."""
        if plugin_name not in self._tool_handlers:
            self._tool_handlers[plugin_name] = {}
        self._tool_handlers[plugin_name][tool_name] = handler

    def is_plugin_enabled(self, plugin_name: str, agent_spec: dict[str, Any]) -> bool:
        """Verify whether the plugin is explicitly enabled in the agent specification.

        Security rule: Permissions must be enforced outside the model.
        """
        spec_body = agent_spec.get("spec", {})
        plugins_list = spec_body.get("plugins", [])

        for p in plugins_list:
            if isinstance(p, dict) and p.get("name") == plugin_name:
                return bool(p.get("enabled", True))

        return False

    async def execute_tool(
        self,
        plugin_name: str,
        tool_name: str,
        args: dict[str, Any],
        agent_spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a plugin tool with permission and safety verification.

        Args:
            plugin_name: Name of the plugin.
            tool_name: Specific tool function to call.
            args: Arguments provided to the tool.
            agent_spec: Target agent spec to verify permissions against.

        Raises:
            PluginNotFoundError: If the plugin is not installed.
            PluginPermissionError: If the plugin is disabled or unapproved.

        """
        manifest = self.get_manifest(plugin_name)

        if agent_spec is not None and not self.is_plugin_enabled(plugin_name, agent_spec):
            raise PluginPermissionError(
                f"Permission denied: Plugin '{plugin_name}' is not enabled in agent spec."
            )

        handlers = self._tool_handlers.get(plugin_name, {})
        handler = handlers.get(tool_name)
        if handler is None:
            raise PluginNotFoundError(f"Tool '{tool_name}' not found for plugin '{plugin_name}'.")

        # Call the tool handler
        result = await handler(**args)

        if isinstance(result, dict) and manifest.untrusted_output:
            result["untrusted"] = True

        return result

    def get_tool_definitions(
        self,
        enabled_plugin_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return LiteLLM / OpenAI compatible function calling definitions."""
        tools: list[dict[str, Any]] = []

        target_plugins = (
            enabled_plugin_names
            if enabled_plugin_names is not None
            else list(self._manifests.keys())
        )

        for name in target_plugins:
            if name == "web-fetch" and "web-fetch" in self._manifests:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": "web_fetch",
                            "description": self._manifests["web-fetch"].description,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string",
                                        "description": "The public HTTP/HTTPS URL to fetch.",
                                    },
                                    "max_chars": {
                                        "type": "integer",
                                        "description": "Max characters of text to extract.",
                                        "default": 10000,
                                    },
                                },
                                "required": ["url"],
                            },
                        },
                    }
                )

            elif name == "web-search" and "web-search" in self._manifests:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "description": self._manifests["web-search"].description,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query string.",
                                    },
                                    "max_results": {
                                        "type": "integer",
                                        "description": "Maximum number of search results.",
                                        "default": 5,
                                    },
                                    "engine": {
                                        "type": "string",
                                        "description": "Search provider engine.",
                                        "enum": ["duckduckgo", "mock"],
                                        "default": "duckduckgo",
                                    },
                                },
                                "required": ["query"],
                            },
                        },
                    }
                )

            elif name == "web-scrape" and "web-scrape" in self._manifests:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": "web_scrape",
                            "description": self._manifests["web-scrape"].description,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string",
                                        "description": "The public HTTP/HTTPS URL to scrape.",
                                    },
                                    "max_chars": {
                                        "type": "integer",
                                        "description": "Max characters of markdown content.",
                                        "default": 25000,
                                    },
                                    "extract_headings": {
                                        "type": "boolean",
                                        "description": "Whether to extract structured headings.",
                                        "default": True,
                                    },
                                    "extract_links": {
                                        "type": "boolean",
                                        "description": "Whether to extract outbound links.",
                                        "default": True,
                                    },
                                },
                                "required": ["url"],
                            },
                        },
                    }
                )

            elif name == "crm-export" and "crm-export" in self._manifests:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": "crm_export",
                            "description": self._manifests["crm-export"].description,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "leads": {
                                        "type": "array",
                                        "description": "List of lead objects to export.",
                                        "items": {"type": "object"},
                                    },
                                    "format": {
                                        "type": "string",
                                        "description": "Target export format.",
                                        "enum": ["csv", "hubspot", "salesforce", "json"],
                                        "default": "csv",
                                    },
                                },
                                "required": ["leads"],
                            },
                        },
                    }
                )

        return tools

    def get_tools_for_plugin(self, plugin_name: str) -> list[str]:
        """Return names of registered tools for a given plugin."""
        return list(self._tool_handlers.get(plugin_name, {}).keys())

    def get_config_schema(self, plugin_name: str) -> dict[str, Any] | None:
        """Parse and return the JSON configuration schema for a plugin if available."""
        manifest = self._manifests.get(plugin_name)
        if not manifest or not manifest.config_schema:
            return None

        schema_path = (self.plugins_dir / plugin_name / manifest.config_schema).resolve()
        if schema_path.exists() and schema_path.is_file():
            try:
                import json

                return json.loads(schema_path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None
