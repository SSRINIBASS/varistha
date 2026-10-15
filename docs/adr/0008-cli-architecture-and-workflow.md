# ADR 0008: CLI Architecture, Client Boundary, and Developer Workflow

## Status
Accepted

## Context
Phase 1, Task 7 of the Varistha roadmap (`docs/SPEC.md § 7.5 Task 7` & `§ 3.4`) requires a command-line interface (`varistha`) to enable the developer workflow:
1. **Spec Scaffolding (`varistha init`)**: Developers must be able to generate a valid, compliant `agent.yaml` without manually writing boilerplate.
2. **Declarative Synchronization (`varistha apply -f <path>`)**: Developers must be able to validate their agent specification locally before hitting the network, and idempotently create or update the agent and its version in the registry.
3. **Run Execution & Watch Mode (`varistha run <id-or-name>`)**: Developers need to trigger execution runs from the terminal, inspect live execution progress, monitor token consumption, USD cost attribution, and capture OpenTelemetry trace IDs for downstream debugging.
4. **Architectural Decoupling**: The CLI package (`packages/cli`) must not import internal API modules or runtime code. All interactions with the Varistha control plane must happen strictly via standard HTTP REST endpoints. The only internal monorepo package allowed is `varistha-spec` for offline schema verification.

## Decision

### 1. Technology Selection: Click and Rich
- **Click**: Chosen for robust POSIX-compliant argument parsing, subcommand nesting, option validation, environment variable fallback (`VARISTHA_API_URL`), and testability via `CliRunner`.
- **Rich**: Provides high-fidelity terminal UI (panels, tables, spinners, colored status markers). To guarantee compatibility across all platforms including legacy Windows command prompts (CP1252), ASCII-safe status indicators (`+`, `-`, `!`, `x`) are utilized.

### 2. Client-Server Architecture & HTTP Client (`varistha_cli.client`)
- **VaristhaClient**: Built atop `httpx.Client`, encapsulating control plane REST APIs:
  - `GET /health`: Health probe.
  - `GET /api/v1/agents/{id}`: Agent lookup by UUID or unique slug.
  - `POST /api/v1/agents`: Agent registration.
  - `POST /api/v1/agents/{id}/versions`: Version publishing.
  - `POST /api/v1/agents/{id}/runs`: Triggering execution runs.
  - `GET /api/v1/runs/{id}`: Run status inspection and trace correlation.
- **Fail-safe Error Handling**: Network failures and HTTP error responses are intercepted and mapped into structured CLI messages without printing Python stack traces.

### 3. Command Workflows

#### `varistha init [NAME]`
- Scaffolds a canonical `agent.yaml` compliant with `varistha-spec` (`AgentSpec`).
- Configurable flags: `--role`, `--owner`, `--model`, `--output/-o`, `--force/-f`.
- Refuses to overwrite existing files unless `--force` is explicitly passed.

#### `varistha apply -f <path>`
- **Offline Validation Gate**: First validates the YAML file locally using `varistha_spec.validate_agent_spec_yaml()`. If schema errors exist, they are displayed in a formatted error panel and execution halts before making network calls.
- **Idempotent Upsert**:
  1. Checks if the agent exists in the registry by name or ID.
  2. If not found (404), registers a new agent with version `v1` via `POST /api/v1/agents`.
  3. If found, publishes a new immutable version via `POST /api/v1/agents/{agent_id}/versions`.

#### `varistha run <id-or-name>`
- Dispatches execution requests via `POST /api/v1/agents/{id}/runs`.
- Accepts structured JSON or raw string inputs (`-i / --input`).
- **Watch Mode (`-w / --watch`)**: Displays a live terminal spinner while polling the run status every `--interval` seconds until a terminal state (`completed`, `failed`, `waiting_approval`) is reached or `--timeout` expires.
- **Summary Presentation**: Renders a clean status panel with execution metadata, token counts (prompt, completion, total), USD cost, duration, trace ID, and agent output.
- **Machine-Readable Mode (`--json`)**: Emits raw JSON for CI/CD pipeline integration and scripting.

## Consequences

### Positive
- Developers have a fast, ergonomic CLI for managing AI agents without opening a browser or writing API client scripts.
- Offline validation catches syntax and schema errors before network transmission.
- Strict architecture boundaries: `packages/cli` depends only on `varistha-spec` and standard HTTP libraries, strictly adhering to `AGENTS.md`.
- Comprehensive test coverage: 37 tests covering all CLI commands, edge cases, connection errors, and rendering formats (94% coverage).

### Negative / Trade-offs
- Polling in watch mode adds small periodic HTTP load to the API. In future phases, Server-Sent Events (SSE) or WebSockets could provide push-based streaming output.
