# ADR 0020: Plugin Manifest Registry, Capability Explorer, and Security Boundary Gating

## Status
Accepted

## Context
Per `docs/SPEC.md § 5 (Phase 5: Plugin ecosystem and role packs)`, `§ 3.1` (Control plane interfaces), `§ 4.4` (UI and design system), and `Appendix A`:
1. **Dynamic Plugin Discovery**: Capabilities must be modular plugins discovered dynamically from plugin directory manifests (`plugins/<name>/manifest.yaml`), rather than hardcoded logic in the core runtime.
2. **Deterministic Security Outside the Model**: Model instructions cannot be trusted to self-enforce tool permissions, scopes, and approval requirements. Governance rules (risk levels, approval policies, rate limits, untrusted output flags) must be enforced deterministically in host middleware.
3. **Operator Observability**: Operators require a comprehensive UI explorer to inspect installed plugins, review permission scopes (`network:read`, `crm:export`, etc.), inspect configuration JSON schemas, and understand untrusted execution boundaries.

## Decision

### 1. Plugin Registry API (`apps/api/src/plugins/`)
- Implemented `PluginHost` discovery helpers:
  - `get_tools_for_plugin(name)`: Enumerates exposed tool functions from plugin manifests and tool definitions.
  - `get_config_schema(name)`: Retrieves the JSON Schema describing plugin configuration properties.
- Added Pydantic response models in `apps/api/src/plugins/schemas.py`:
  - `PluginInfoResponse`: Structured plugin manifest including `name`, `version`, `description`, `transport` (`in-process`, `mcp-stdio`, `mcp-sse`), `risk` (`low`, `medium`, `high`), `scopes`, `requires_approval`, `untrusted_output`, `config_schema`, and `tools`.
  - `PluginListResponse`: Paginated/total list of installed plugins.
- Added REST router in `apps/api/src/plugins/router.py`:
  - `GET /api/v1/plugins`: Lists all discovered plugins with risk, approval requirements, scopes, and tools.
  - `GET /api/v1/plugins/{name}`: Fetches detailed plugin metadata and configuration schema.

### 2. Frontend UI Explorer (`apps/ui/`)
- Added semantic domain models and API clients in `apps/ui/src/lib/types.ts` and `apps/ui/src/lib/api.ts` (`getPlugins`, `getPlugin`).
- Added semantic status badges in `apps/ui/src/components/badges.tsx`:
  - `PluginRiskBadge`: Renders `low`, `medium`, and `high` risk badges using semantic color tokens.
  - `ApprovalRequiredBadge`: Clearly indicates whether plugin execution requires human-in-the-loop signoff or is auto-executable.
- Created `apps/ui/src/components/plugins/plugin-card.tsx`:
  - Renders plugin name, version, transport type, risk badge, approval badge, untrusted output quarantine indicator, description, scopes, and tool chips.
- Created `apps/ui/src/components/plugins/plugin-inspector.tsx`:
  - Modal inspector with tabbed navigation:
    1. **Governance & Capabilities**: Displays risk level, transport, scopes, output quarantine alerts, and exposed tool functions.
    2. **Config Schema**: Syntax-formatted JSON Schema viewer for plugin configuration.
    3. **Raw Manifest**: Copyable JSON manifest payload.
- Created `apps/ui/src/components/plugins/plugin-explorer.tsx`:
  - Responsive search bar (by name, description, scope, or tool).
  - Multi-dimensional filtering by risk level, transport mechanism, and approval policy.
  - Filter reset capabilities and empty state handling.
- Created `apps/ui/src/app/plugins/page.tsx`:
  - Top-level page featuring metric summary cards (Total Plugins, Low Risk, Approval Gated, Untrusted Output Quarantined).
  - Subnav underline tabs switching between Plugin Directory and Security Architecture documentation.
- Integrated `Plugins` navigation item with `Blocks` icon in `apps/ui/src/components/navbar.tsx`.

## Consequences
- **Positive**: Operators have a centralized control plane view of all installed capabilities and their security postures.
- **Positive**: Strict adherence to the security principle that tool permissions and untrusted output flags are deterministic and inspected outside the model.
- **Positive**: Full test coverage (97% in backend plugins module, 48 UI unit tests passing) and zero architectural boundary violations (`scripts/check_boundaries.py` clean).
