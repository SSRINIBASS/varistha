# Milestone Checkpoint: Phase 1, Task 5 — MCP Plugin Host & web-fetch with SSRF Protection

- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 5 — MCP plugin host and the `web-fetch` plugin with SSRF protection
- **Status**: PASSED
- **Timestamp**: 2026-10-15T14:30:00+05:30
- **Git Commit**: `0f98340`
- **Reference Spec**: `docs/SPEC.md § 7.5 Task 5, § 3.5 & § 4.1`

---

## 1. Implemented Capabilities

1. **Plugin Manifest Specification (`apps/api/src/plugins/manifest.py`, `plugins/web-fetch/plugin.yaml`)**:
   - Declarative manifest defining plugin metadata (`name`, `version`, `description`, `transport`, `risk`, `scopes`, `requires_approval`, `untrusted_output`, `config_schema`).
   - JSON Schema for plugin configuration (`plugins/web-fetch/config.schema.json`).

2. **Strict Multi-Layer SSRF Defense (`plugins/web-fetch/ssrf.py`)**:
   - `validate_url_against_ssrf(url)` validates scheme (`http`, `https`), rejects embedded credentials, and resolves hostnames via DNS.
   - Evaluates all resolved IPv4 and IPv6 addresses against comprehensive CIDR blocklist:
     - Loopback (`127.0.0.0/8`, `::1/128`)
     - Private RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
     - Link-local and cloud metadata (`169.254.0.0/16`, `169.254.169.254`, `fe80::/10`)
     - Carrier-grade NAT (`100.64.0.0/10`), documentation IPs, multicast, and broadcast.
   - Re-checks target URLs at every redirect step to prevent open redirect SSRF attacks.

3. **Web Page Fetcher (`plugins/web-fetch/fetcher.py`)**:
   - Fetches web pages safely using `httpx.AsyncClient` with custom timeouts and user-agent.
   - Cleanly extracts HTML `<title>` and strips scripts, styles, and markup.
   - Enforces character truncation (`max_chars`).
   - Returns structured dictionary explicitly flagged with `"untrusted": True`.

4. **Plugin Host (`apps/api/src/plugins/host.py`)**:
   - Scans and loads plugin manifests from `plugins/` directory.
   - Enforces permissions outside the language model: checks whether `AgentSpec.plugins` enables the plugin before allowing tool execution.
   - Formats tool definitions into standard OpenAI/LiteLLM function schemas.

---

## 2. Test & Quality Metrics

- **Unit & Security Tests Added**: 37 tests (29 SSRF security tests, 4 web fetcher tests, 4 plugin host tests).
- **Cumulative Tests**: 106 passing tests across the monorepo.
- **Test Coverage**:
  - `plugins/web-fetch/`: 93% (`fetcher.py`: 95%, `ssrf.py`: 84%, `conftest.py`: 100%, `test_fetcher.py`: 100%, `test_ssrf.py`: 100%).
  - `apps/api/src/plugins/`: 96% (`host.py`: 95%, `manifest.py`: 100%, `test_host.py`: 100%).
  - Monorepo overall test coverage: 98% (exceeds ≥ 80% gate).
- **Linter Status**: `ruff check` clean (0 errors).
- **Format Status**: `ruff format --check` clean (0 errors).
- **Type Checker Status**: `pyright` strict clean (0 errors, 0 warnings).
- **Architecture Boundaries**: `check_boundaries.py` clean (0 cross-context violations, no hardcoded tool logic in core).
- **Architectural Decision Record**: `docs/adr/0006-mcp-plugin-host-and-ssrf-protection.md`.

---

## 3. Artifact Manifest

- `plugins/web-fetch/plugin.yaml`: Manifest for web-fetch plugin.
- `plugins/web-fetch/config.schema.json`: JSON Schema for web-fetch.
- `plugins/web-fetch/ssrf.py`: SSRF validation logic and CIDR filters.
- `plugins/web-fetch/fetcher.py`: Asynchronous web page content fetcher.
- `plugins/web-fetch/__init__.py`: Plugin module exports.
- `plugins/web-fetch/tests/conftest.py`: Test fixtures and path setup.
- `plugins/web-fetch/tests/test_ssrf.py`: 29 security test cases for SSRF protection.
- `plugins/web-fetch/tests/test_fetcher.py`: Tests for HTML extraction and redirection defense.
- `apps/api/src/plugins/manifest.py`: Pydantic PluginManifest model.
- `apps/api/src/plugins/host.py`: Plugin discovery, permission checks, and execution host.
- `apps/api/src/plugins/__init__.py`: Package exports.
- `apps/api/src/plugins/tests/test_host.py`: Tests for plugin host and permission enforcement.
- `docs/plans/phase-1-task-5-plugins.md`: Implementation plan.
- `docs/adr/0006-mcp-plugin-host-and-ssrf-protection.md`: ADR 0006.
- `docs/checkpoints/2026-10-15-phase-1-task-5-plugins.md`: Milestone checkpoint.

---

## 4. Known Gaps & Next Steps

- **Current State**: Phase 1 Tasks 1 through 5 are complete and verified.
- **Next Task**: Phase 1, Task 6 — OTel instrumentation, an OTLP receiver in the API, and span persistence (`docs/SPEC.md § 7.5 Task 6 & § 4.3`).
