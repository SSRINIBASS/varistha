# Plugin Authoring Guide

All external capabilities in Varistha (web fetching, scraping, email drafting, API calls) are implemented as **Model Context Protocol (MCP)** plugins. No hardcoded tool logic resides in the core control plane.

---

## 1. Plugin Architecture

Varistha discovers plugins located in the `plugins/` directory. Each plugin must define:
- A `manifest.json` describing metadata, exposed tools, risk tier, and configuration schemas.
- An MCP server implementation exposing tools over JSON-RPC or native Python async calls.

```
plugins/my-custom-plugin/
├── manifest.json        # Plugin declaration and JSON schema
├── __init__.py
├── server.py            # Tool implementations
└── tests/
    └── test_server.py   # Unit test suite
```

---

## 2. Manifest Specification (`manifest.json`)

```json
{
  "$schema": "https://varistha.dev/schemas/plugin-manifest.v1.json",
  "name": "company-enrichment",
  "version": "0.1.0",
  "description": "Enriches company domains with employee counts, revenue, and industry tags.",
  "license": "Apache-2.0",
  "risk_level": "low",
  "scopes": ["enrichment:read"],
  "untrusted_output": true,
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "description": "API key for enrichment data provider"
      }
    },
    "required": ["api_key"]
  },
  "tools": [
    {
      "name": "lookup_company",
      "description": "Fetch company profile by domain name.",
      "input_schema": {
        "type": "object",
        "properties": {
          "domain": {
            "type": "string",
            "description": "Clean domain name (e.g., stripe.com)"
          }
        },
        "required": ["domain"]
      }
    }
  ]
}
```

### Risk Level Guidelines
- **`low`**: Read-only lookup operations with zero side effects.
- **`medium`**: Operations that write non-sensitive internal data (e.g. CRM drafts, local cache).
- **`high`**: Outbound external actions (e.g. sending emails, posting to social networks, initiating financial transactions). **High-risk plugins require explicit approval at Autonomy L1 and below.**

---

## 3. Server Implementation (`server.py`)

Tools are written as asynchronous Python functions:

```python
"""Company enrichment MCP plugin tool implementation."""

from typing import Any
import httpx


async def lookup_company(domain: str, config: dict[str, Any]) -> dict[str, Any]:
    """Look up verified firmographic data for a target domain."""
    api_key = config.get("api_key")
    if not api_key:
        raise ValueError("Missing 'api_key' in plugin configuration")

    # Clean domain
    clean_domain = domain.lower().strip().removeprefix("https://").removeprefix("http://")

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"https://api.example.com/v1/companies/{clean_domain}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        return resp.json()
```

---

## 4. Security Rules (Mandatory)

1. **SSRF Safeguards for Fetch / Scrape Plugins**:
   Any plugin that performs HTTP requests to user-provided URLs must validate that the target IP does not resolve to private, loopback, or link-local ranges:
   - `127.0.0.0/8` (Loopback)
   - `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` (Private RFC 1918)
   - `169.254.0.0/16` (Cloud link-local metadata)
2. **Untrusted Data Flagging**:
   All web content, email bodies, and user inputs returned by tools must be labeled with `"untrusted_output": true`. The control plane guarantees that untrusted outputs cannot override system instructions or alter tool permissions.
3. **No Scraping Evasion**:
   Do not implement CAPTCHA bypass, fake browser fingerprinting, or terms-of-service circumvention.
4. **License Compliance**:
   Core plugins must use OSI-approved licenses (Apache-2.0, MIT, BSD).
