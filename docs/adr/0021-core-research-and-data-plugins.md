# ADR 0021: Core Research & Data Plugins (Web-Search, Web-Scrape, CRM-Export)

## Status
Accepted

## Context
In accordance with `docs/SPEC.md § 5 (Phase 5: Plugin ecosystem and role packs)`:
1. **Research Capabilities**: Role packs for sales intelligence and market research require searching the web for company news, extracting structured markdown content from public blogs and websites, and exporting discovered leads to CRM systems.
2. **SSRF and Untrusted Execution Boundaries**: Web requests must strictly enforce SSRF protection to prevent access to loopback (127.0.0.0/8), RFC 1918 private ranges, and cloud instance metadata (169.254.169.254). Output from web search and scrape plugins must be labeled `untrusted: true` to prevent prompt injection and untrusted instruction poisoning.
3. **No Scraping Evasion**: In adherence to `docs/SPEC.md § A.12`, Varistha strictly refuses scraping evasion, CAPTCHA bypass, and ToS circumvention.

## Decision

### 1. `web-search` Plugin (`plugins/web-search/`)
- Implemented `search_web` querying public DuckDuckGo HTML results with structured citation extraction:
  - Extracted fields: `title`, `url` (unquoting `uddg` redirect parameters), and `snippet`.
  - Built-in `mock` engine support for deterministic offline and CI testing.
  - Returns `untrusted_output: true` with strict rate limits and network timeout handling.

### 2. `web-scrape` Plugin (`plugins/web-scrape/`)
- Implemented `scrape_url` providing deep article and webpage content extraction:
  - Strict SSRF defense on all initial and redirected HTTP requests (`SSRFSecurityError`).
  - Converts HTML body into readable, clean markdown, stripping `<script>`, `<style>`, `<nav>`, `<footer>`, and ads.
  - Extracts page `<title>`, `<meta name="description">`, headings (`h1` to `h3`), and outbound HTTP/HTTPS links.
  - Returns `untrusted_output: true`.

### 3. `crm-export` Plugin (`plugins/crm-export/`)
- Implemented `export_leads` supporting multiple enterprise formats:
  - `csv`: Generates standard CSV with header row and key normalization.
  - `hubspot`: Generates HubSpot Batch Contacts payload with mapped contact properties.
  - `salesforce`: Generates Salesforce Lead sObject payload.
  - `json`: Returns raw verified lead dictionary array.
  - Strictly validates that each lead record has at least one identifying property (`email`, `company`, or `name`).

### 4. Integration with `PluginHost` (`apps/api/src/plugins/host.py`)
- Registered handlers for `web_search`, `web_scrape`, and `crm_export`.
- Added OpenAI/LiteLLM function calling schemas in `get_tool_definitions()`.

## Consequences
- **Positive**: Complete set of research and export plugins available for sales and competitor intelligence role pack agents.
- **Positive**: Strict SSRF defenses protect against cloud credential leakage and local host probing.
- **Positive**: Full test coverage (61 tests in plugins suite, 345 total pytest tests passing) with zero boundary violations.
