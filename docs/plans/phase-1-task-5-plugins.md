# Implementation Plan: Phase 1, Task 5 — MCP Plugin Host & web-fetch with SSRF Protection

## Task Information
- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 5 — MCP plugin host and the `web-fetch` plugin with SSRF protection (`docs/SPEC.md § 7.5 Task 5` & `§ 3.5, § 4.1`)
- **Estimated Scope**: ~450-550 lines across 8 files

---

## 1. Context & Objectives

Per `AGENTS.md` and `docs/SPEC.md`:
1. **MCP Plugins**: All capabilities are exposed as plugins described by a plugin manifest (`plugin.yaml`). No hardcoded tool logic in core.
2. **SSRF Protection (Hard Requirement)**: Fetch and scrape plugins must block private, loopback, link-local, and cloud metadata address ranges (e.g., `127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`, `::1`).
3. **Untrusted Data Isolation**: Content fetched from the web is untrusted data. Plugins declare `untrusted_output: true`, ensuring content cannot hijack system prompts or bypass tool permissions.
4. **Permissions Enforced Outside Model**: The plugin host enforces whether a plugin is enabled in the agent spec before executing tool calls.

---

## 2. Component Design

### 2.1 SSRF Defense (`plugins/web-fetch/ssrf.py`)
- DNS resolution of hostnames to IP addresses (IPv4 & IPv6).
- Rejects non-HTTP/HTTPS protocols (`file:`, `ftp:`, `gopher:`).
- Checks all resolved IPs against blocked CIDR networks:
  - Loopback (`127.0.0.0/8`, `::1/128`)
  - Private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`)
  - Link-local / Cloud metadata (`169.254.0.0/16`, `fe80::/10`)
  - Broadcast / reserved (`0.0.0.0/8`, `224.0.0.0/4`, `240.0.0.0/4`)
- Raises typed `SSRFSecurityError`.

### 2.2 `web-fetch` Plugin (`plugins/web-fetch/`)
- `plugin.yaml`: Manifest with `name: web-fetch`, `risk: low`, `scopes: [network:read]`, `untrusted_output: true`.
- `config.schema.json`: JSON schema for plugin config.
- `fetcher.py`: Performs HTTP request via `httpx.AsyncClient` with SSRF pre-check and timeout. Extracts readable text / HTML title, returning structured payload with `untrusted: True`.

### 2.3 Plugin Host & Registry (`apps/api/src/plugins/`)
- `manifest.py`: Pydantic `PluginManifest` model.
- `host.py`: `PluginHost` service that:
  - Scans `plugins/` directory for manifests.
  - Registers available plugins and their tool schemas.
  - Enforces agent spec permissions (checks if `spec.plugins` has `name` and `enabled: true`).
  - Executes tool functions safely.

### 2.4 Integration with Runtime
- Runtime adapter can inject available tools into the LangGraph graph or execute tool calls.

---

## 3. Files to Create / Modify

| File | Purpose |
| :--- | :--- |
| `plugins/web-fetch/plugin.yaml` | Plugin manifest for `web-fetch` |
| `plugins/web-fetch/config.schema.json` | Configuration JSON Schema |
| `plugins/web-fetch/ssrf.py` | Strict IP / CIDR validation & DNS check |
| `plugins/web-fetch/fetcher.py` | Asynchronous web page fetching & text extraction |
| `apps/api/src/plugins/manifest.py` | Pydantic model for plugin manifests |
| `apps/api/src/plugins/host.py` | Plugin discovery and execution host |
| `apps/api/src/plugins/__init__.py` | Package exports |
| `plugins/web-fetch/tests/test_ssrf.py` | Comprehensive SSRF security test suite |
| `plugins/web-fetch/tests/test_fetcher.py` | Web fetching and extraction tests |
| `apps/api/src/plugins/tests/test_host.py` | Plugin discovery and permission gate tests |

---

## 4. Verification & Quality Gates

1. **Unit & Security Tests**:
   - SSRF blocks `localhost`, `127.0.0.1`, `::1`, `169.254.169.254`, `10.0.0.1`, `192.168.1.1`, `172.16.0.1`.
   - SSRF rejects non-http protocols (`file:///etc/passwd`, `ftp://`).
   - SSRF allows valid public domains (`https://example.com`).
   - Web fetcher returns clean text and marks `untrusted: True`.
   - Plugin host discovers `web-fetch` plugin manifest.
   - Plugin host denies tool execution if agent spec has disabled plugin.
2. **Acceptance Gates**:
   - `ruff check .` clean.
   - `ruff format --check .` clean.
   - `pyright apps/ packages/ plugins/` clean.
   - `check_boundaries.py` clean (no hardcoded tool logic in core).
   - Test coverage ≥ 80%.
