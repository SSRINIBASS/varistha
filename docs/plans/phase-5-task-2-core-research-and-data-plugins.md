# Implementation Plan: Phase 5, Task 2 — Core Research & Data Plugins

## Context & Objectives
In accordance with `docs/SPEC.md § 5 (Phase 5: Plugin ecosystem and role packs)`:
- **Goal**: Implement the foundational research and data plugins required by the Sales and Market Intelligence role packs:
  1. `web-search`: Pluggable web search returning structured citations, titles, and snippets.
  2. `web-scrape`: Deep page and article content extractor converting HTML to clean markdown with metadata and SSRF validation.
  3. `crm-export`: Lead and account exporter to CSV and standard CRM payloads (HubSpot, Salesforce).
- **Security Rule**:
  - `web-search` and `web-scrape` are flagged `untrusted_output: true`.
  - All web plugins enforce strict SSRF validation (blocking loopback, RFC 1918 private IPs, and cloud metadata).
  - No scraping evasion, CAPTCHA bypass, or ToS circumvention (`SPEC.md § A.12`).
  - Tool execution and permissions enforced deterministically in `PluginHost` outside the model.

---

## 1. Files to Touch / Create

### Plugins Directory
- `plugins/web-search/`:
  - `plugin.yaml`: Manifest declaration.
  - `config.schema.json`: Configuration schema (`engine`, `max_results`, `timeout_seconds`).
  - `searcher.py`: Search execution logic with structured results and mock support.
  - `__init__.py`: Public exports.
  - `tests/test_searcher.py`: Unit tests for query execution, formatting, and engine fallbacks.
- `plugins/web-scrape/`:
  - `plugin.yaml`: Manifest declaration.
  - `config.schema.json`: Configuration schema (`max_chars`, `extract_headings`, `extract_links`).
  - `scraper.py`: Content extraction, markdown conversion, and SSRF validation.
  - `__init__.py`: Public exports.
  - `tests/test_scraper.py`: Unit tests verifying SSRF protection, heading extraction, and clean text extraction.
- `plugins/crm-export/`:
  - `plugin.yaml`: Manifest declaration.
  - `config.schema.json`: Configuration schema (`default_format`).
  - `exporter.py`: CSV, HubSpot, and Salesforce formatting and field validation.
  - `__init__.py`: Public exports.
  - `tests/test_exporter.py`: Unit tests verifying lead schema validation and payload generation.

### Core Plugin Host Integration
- `apps/api/src/plugins/host.py`:
  - Register built-in handlers for `web-search`, `web-scrape`, and `crm-export`.
  - Add LiteLLM function calling definitions in `get_tool_definitions()`.
- `apps/api/src/plugins/tests/test_host.py`:
  - Integration tests for executing new tools through `PluginHost.execute_tool()`.

### Documentation & Decisions
- `docs/adr/0021-core-research-and-data-plugins.md`: Architecture Decision Record for research and data plugins.
- `CHANGELOG.md`: Record Task 2 deliverables.

---

## 2. Acceptance Criteria & Exit Gate
1. All 3 plugins are discovered dynamically by `PluginHost.discover_plugins()`.
2. `web-search` executes queries and returns structured citations with `untrusted: true`.
3. `web-scrape` rejects private/loopback/cloud-metadata URLs with `SSRFSecurityError` and extracts clean markdown from valid public pages.
4. `crm-export` validates lead schemas and outputs valid CSV, HubSpot, and Salesforce payloads.
5. All test suites pass: `pytest` (backend & plugins), `pyright`, `ruff`, and UI test suite.
