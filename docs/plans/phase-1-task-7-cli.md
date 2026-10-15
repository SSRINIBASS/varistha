# Implementation Plan: Phase 1, Task 7 — CLI Commands (`init`, `apply`, `run`)

## 1. Task Restatement & Exit Criteria
- **Task**: Phase 1, Task 7 of the Varistha roadmap (`docs/SPEC.md § 7.5 Task 7` & `§ 5`).
- **Goal**: Implement the `varistha` CLI in `packages/cli` providing three core commands:
  1. `varistha init`: Scaffolds a production-ready starter `agent.yaml` compliant with `varistha-spec`.
  2. `varistha apply -f <path>`: Validates the agent spec locally via `varistha-spec` and creates or updates the agent version in the Varistha API registry.
  3. `varistha run <id-or-name>`: Triggers an agent run with optional input, displaying real-time execution status, token usage, cost attribution, and trace ID.
- **Exit Criteria**: A YAML file can be created via `varistha init`, applied via `varistha apply -f agent.yaml`, and executed via `varistha run`, producing an executed agent run with full trace visibility in the database.

---

## 2. Dependencies & Licenses
All dependencies in `packages/cli/pyproject.toml` are OSI-approved:
- `click>=8.1`: BSD-3-Clause (Standard Python CLI framework)
- `httpx>=0.27`: BSD-3-Clause (Async and sync HTTP client)
- `pyyaml>=6.0`: MIT (YAML parsing and serialization)
- `rich>=13.0`: MIT (Terminal formatting, tables, panels, and spinners)
- `varistha-spec`: Apache-2.0 (Workspace package for AgentSpec models and validator)

---

## 3. Package Structure & Architectural Boundaries
```
packages/cli/
├── pyproject.toml                     # Configure script `varistha = "varistha_cli.main:main"`
├── src/
│   └── varistha_cli/
│       ├── __init__.py                # Package exports
│       ├── main.py                    # Root Click group, `--api-url`, `--version`
│       ├── client.py                  # API HTTP client with error handling
│       ├── display.py                 # Rich console styling, tables, error boxes
│       ├── templates.py               # Starter agent spec YAML template
│       └── commands/
│           ├── __init__.py
│           ├── init_cmd.py            # `init` implementation
│           ├── apply_cmd.py           # `apply` implementation
│           └── run_cmd.py             # `run` implementation
└── tests/
    ├── conftest.py                    # Test fixtures & CliRunner setup
    ├── test_init.py                   # Unit tests for `varistha init`
    ├── test_apply.py                  # Unit tests for `varistha apply`
    ├── test_run.py                    # Unit tests for `varistha run`
    └── test_cli.py                    # Root CLI tests (help, version, global options)
```

### Architectural Guardrails
- `packages/cli` communicates with the Varistha control plane exclusively over HTTP (`httpx`) using standard REST endpoints (`POST /api/v1/agents`, `POST /api/v1/agents/{id_or_name}/runs`, etc.).
- `packages/cli` imports `varistha-spec` for offline schema validation.
- `packages/cli` does **NOT** import `apps/api` internals (`registry`, `runtime`, `shared.db`), maintaining clean client-server decoupling.

---

## 4. Command Specifications

### 4.1 `varistha init`
- **Signature**: `varistha init [OPTIONS] [NAME]`
- **Arguments/Options**:
  - `NAME`: Optional agent name (default: `my-agent`).
  - `-o, --output PATH`: Target file path (default: `agent.yaml` or `<name>.yaml`).
  - `-f, --force`: Overwrite target file if it already exists.
  - `--role ROLE`: Starter role description.
- **Behavior**:
  - Writes a valid YAML spec matching `AgentSpec` schema:
    ```yaml
    apiVersion: varistha/v1
    kind: Agent
    metadata:
      name: lead-researcher
      owner: team@startup.com
      stage: dev
      version: 0.1.0
    spec:
      role: Researches inbound leads and enriches company profiles
      model:
        primary: gpt-4o-mini
        fallback: gpt-3.5-turbo
      instructions: |
        Analyze the lead's domain and company details.
        Summarize core business, key executives, and target market.
      autonomy: L1
      plugins:
        - name: web-fetch
          enabled: true
      budget:
        per_run_usd: 0.50
        per_day_usd: 10.00
    ```
  - Displays formatted confirmation and prints the next step (`varistha apply -f <path>`).

### 4.2 `varistha apply`
- **Signature**: `varistha apply -f, --file PATH [OPTIONS]`
- **Behavior**:
  - Reads YAML file at `PATH`.
  - Runs local validation via `varistha-spec.validate_spec_yaml()`.
  - If validation fails, prints errors in a red panel with exact location paths and exits with code 1 without calling the API.
  - If valid:
    - Queries API: `GET /api/v1/agents/{name}`.
    - If agent does not exist: calls `POST /api/v1/agents` with the raw spec.
    - If agent exists: calls `POST /api/v1/agents/{name}/versions` with the spec.
  - Renders a Rich panel with Agent details: Name, Version, Stage, Autonomy, Primary Model, and UUID.

### 4.3 `varistha run`
- **Signature**: `varistha run [OPTIONS] AGENT_ID_OR_NAME`
- **Arguments/Options**:
  - `AGENT_ID_OR_NAME`: Target agent identifier.
  - `-i, --input TEXT`: Input query/prompt for the run (default: `"Execute default task"`).
  - `-w, --watch / --no-watch`: Wait and poll for completion (default: `--watch`).
  - `--timeout SECONDS`: Max polling time in seconds (default: 60).
  - `--json`: Output raw JSON response.
- **Behavior**:
  - Calls `POST /api/v1/agents/{id_or_name}/runs` with `{"trigger_type": "manual", "input": {"query": input}}`.
  - If `--no-watch`: Prints Run ID and status `running`, then exits.
  - If `--watch`: Polls `GET /api/v1/runs/{id}` with exponential backoff until terminal state (`completed`, `failed`, `waiting_approval`).
  - Displays run summary: Run ID, Status, Duration, Tokens (prompt/completion/total), Cost USD, Output summary, and Trace ID.

---

## 5. Test Plan (TDD)
1. **`test_init.py`**:
   - `test_init_creates_default_agent_yaml`: Checks file creation and validates created YAML with `validate_spec_yaml`.
   - `test_init_custom_name_and_output`: Custom name and custom file path.
   - `test_init_fails_if_file_exists`: Raises warning and aborts unless `--force` is provided.
   - `test_init_force_overwrites`: Overwrites existing file when `--force` is used.
2. **`test_apply.py`**:
   - `test_apply_missing_file`: Error when file does not exist.
   - `test_apply_invalid_yaml_syntax`: Schema/YAML parse error shown without API call.
   - `test_apply_spec_validation_failure`: Missing required fields rejected with clean CLI output.
   - `test_apply_creates_new_agent`: Mocked API returns 201; checks CLI output format.
   - `test_apply_creates_new_version_when_exists`: Existing agent triggers version endpoint.
   - `test_apply_api_connection_error`: Friendly error when API server is unreachable.
3. **`test_run.py`**:
   - `test_run_triggers_and_watches_completion`: Triggers run, polls mock API, renders results.
   - `test_run_nowatch_returns_run_id`: Exits immediately after trigger when `--no-watch` is passed.
   - `test_run_failed_status`: Displays failure error message.
   - `test_run_waiting_approval`: Displays waiting approval alert.
   - `test_run_json_output`: Outputs valid JSON.
4. **`test_cli.py`**:
   - `test_cli_help`: `--help` lists `init`, `apply`, `run`.
   - `test_cli_version`: `--version` prints version.
   - `test_cli_api_url_option`: Custom API URL passed to client.

---

## 6. Acceptance & Gate Checklist
- [ ] All new tests pass with `uv run pytest packages/cli/tests`.
- [ ] Test coverage for `packages/cli` exceeds ≥ 80%.
- [ ] `uv run ruff check` clean.
- [ ] `uv run ruff format --check` clean.
- [ ] `uv run pyright` strict clean with 0 errors.
- [ ] `scripts/check_boundaries.py` clean.
- [ ] Smoke test: `varistha init`, `varistha apply -f agent.yaml`, and `varistha run` against local API.
