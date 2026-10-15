"""OpenAI/LiteLLM function calling schemas for built-in core plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plugins.manifest import PluginManifest


def build_tool_definition(plugin_name: str, manifest: PluginManifest) -> dict[str, Any] | None:
    """Return LiteLLM / OpenAI compatible function schema for a given plugin."""
    if plugin_name == "web-fetch":
        return {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": manifest.description,
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

    if plugin_name == "web-search":
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": manifest.description,
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

    if plugin_name == "web-scrape":
        return {
            "type": "function",
            "function": {
                "name": "web_scrape",
                "description": manifest.description,
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

    if plugin_name == "crm-export":
        return {
            "type": "function",
            "function": {
                "name": "crm_export",
                "description": manifest.description,
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

    if plugin_name == "email-draft":
        return {
            "type": "function",
            "function": {
                "name": "email_draft",
                "description": manifest.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Target recipient email address.",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Subject line with optional {{tokens}}.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Main body text with optional {{tokens}}.",
                        },
                        "recipient_name": {
                            "type": "string",
                            "description": "Recipient name for greeting.",
                        },
                        "tone": {
                            "type": "string",
                            "enum": ["professional", "friendly", "persuasive", "concise"],
                            "default": "professional",
                            "description": "Writing style and tone.",
                        },
                        "sender_name": {
                            "type": "string",
                            "description": "Sender name for sign-off.",
                        },
                        "call_to_action": {
                            "type": "string",
                            "description": "Specific closing call to action.",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
            },
        }

    if plugin_name == "email-send":
        return {
            "type": "function",
            "function": {
                "name": "email_send",
                "description": manifest.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Target recipient email address.",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Plain text email body.",
                        },
                        "from_email": {
                            "type": "string",
                            "description": "Sender email address.",
                        },
                        "dry_run": {
                            "type": "boolean",
                            "default": True,
                            "description": "When true, simulates delivery without sending.",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
            },
        }

    if plugin_name == "x-post":
        return {
            "type": "function",
            "function": {
                "name": "x_post",
                "description": manifest.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Post content up to 280 characters.",
                        },
                        "reply_to_id": {
                            "type": "string",
                            "description": "Optional parent tweet ID to reply to.",
                        },
                        "mock": {
                            "type": "boolean",
                            "default": True,
                            "description": "When true, simulates posting.",
                        },
                    },
                    "required": ["text"],
                },
            },
        }

    if plugin_name == "linkedin-post":
        return {
            "type": "function",
            "function": {
                "name": "linkedin_post",
                "description": manifest.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Post commentary up to 3000 characters.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of shared article.",
                        },
                        "article_url": {
                            "type": "string",
                            "description": "URL of article to share.",
                        },
                        "visibility": {
                            "type": "string",
                            "enum": ["PUBLIC", "CONNECTIONS"],
                            "default": "PUBLIC",
                            "description": "Post visibility setting.",
                        },
                        "mock": {
                            "type": "boolean",
                            "default": True,
                            "description": "When true, simulates posting.",
                        },
                    },
                    "required": ["text"],
                },
            },
        }

    return None
