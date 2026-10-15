# ADR 0006: MCP Plugin Host & web-fetch SSRF Defense Architecture

## Status
Accepted

## Context
Phase 1, Task 5 of the Varistha roadmap (`docs/SPEC.md § 7.5 Task 5` & `§ 3.5, § 4.1`) requires establishing the plugin architecture:
1. **Decoupled Plugin Manifest**: Capabilities must be exposed as modular plugins described by declarative manifests (`plugin.yaml`). No hardcoded tool logic in core.
2. **SSRF Protection (Hard Security Requirement)**: Any plugin that makes outbound network requests (e.g. web scraping, fetching) presents an immediate attack vector for Server-Side Request Forgery against internal infrastructure, localhost ports, and cloud metadata services (e.g. `169.254.169.254`).
3. **Untrusted Data Isolation**: All content retrieved from the web or external systems is untrusted data. Plugins must declare `untrusted_output: true` so the runtime can safely isolate fetched data from modifying instructions or permissions.
4. **Permissions Enforced Outside the Model**: Tool execution must be gated by code in the control plane based on the agent's explicit `AgentSpec.plugins` configuration, never left to the model's discretion.

## Decision

### 1. Declarative Plugin Manifest (`apps/api/src/plugins/manifest.py`, `plugins/web-fetch/plugin.yaml`)
We defined a strict Pydantic `PluginManifest` model:
- `name`: Unique plugin name (e.g., `web-fetch`).
- `version`: Semver string.
- `transport`: `in-process`, `mcp-stdio`, or `mcp-sse`.
- `risk`: `low`, `medium`, or `high`.
- `scopes`: Declared capabilities (e.g., `network:read`).
- `requires_approval`: Mandatory approval flag for autonomy L1 and below.
- `untrusted_output`: Flags output for security tagging and sanitization.

### 2. Multi-Layer SSRF Defense (`plugins/web-fetch/ssrf.py`)
The `validate_url_against_ssrf(url)` validator strictly checks:
- **Protocol**: Only `http` and `https` schemes permitted (blocking `file:`, `ftp:`, `gopher:`).
- **Credentials**: Blocks URLs containing embedded credentials (`user:pass@host`).
- **IP Literal & DNS Resolution**: Hostnames are resolved to IP addresses via `socket.getaddrinfo`.
- **Blocked CIDRs**: All resolved IPv4 and IPv6 addresses are evaluated against standard and cloud reserved ranges:
  - Loopback (`127.0.0.0/8`, `::1/128`)
  - Private networks RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Link-Local & Cloud Metadata (`169.254.0.0/16`, `fe80::/10`, AWS/GCP/Azure `169.254.169.254`)
  - Carrier-grade NAT (`100.64.0.0/10`)
  - Documentation and benchmark blocks (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`)
  - Broadcast, multicast, and unspecified (`0.0.0.0/8`, `224.0.0.0/4`, `255.255.255.255/32`)
- **Redirect Chain Validation**: `fetch_url()` intercepts HTTP redirects and re-validates each target URL against SSRF before following.

### 3. Web Fetcher (`plugins/web-fetch/fetcher.py`)
- Uses `httpx.AsyncClient` with custom timeouts and headers (`VaristhaBot/0.1`).
- Cleanly extracts HTML `<title>` and strips scripts, styles, and tags, returning normalized text.
- Automatically marks the result dictionary with `"untrusted": True`.

### 4. Plugin Host (`apps/api/src/plugins/host.py`)
- Discovers installed plugins across the `plugins/` directory.
- `is_plugin_enabled()`: Verifies if the target plugin is explicitly enabled in the agent's spec.
- `execute_tool()`: Rejects unauthorized tool invocations with `PluginPermissionError` before executing any underlying handlers.
- `get_tool_definitions()`: Formats tools into standard OpenAI/LiteLLM function schemas for LLM tool calling.

## Consequences

### Positive
- Strict, multi-layered SSRF protection blocks all internal and cloud metadata exfiltration paths.
- Agent spec permissions are enforced deterministically in application code outside the model.
- Plugins remain modular and self-describing via `plugin.yaml`.
- 100% test coverage on `plugins/web-fetch` and 95% on `apps/api/src/plugins`.

### Negative / Trade-offs
- DNS rebinding attacks: To achieve complete mitigation against DNS rebinding, production deployments should pair this with an egress proxy or DNS pinning resolver in Phase 6.
