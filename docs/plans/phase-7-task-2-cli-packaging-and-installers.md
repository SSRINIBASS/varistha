# Plan: Phase 7 Task 2 — CLI Packaging & One-Line Installers

## Objective
Provide robust, zero-friction distribution and installation tooling for the Varistha CLI (`varistha`) on Linux, macOS, and Windows via standalone scripts and package definitions as specified in `docs/SPEC.md § 6`.

## Scope of Changes
1. **One-Line POSIX Installer (`scripts/install.sh`)**:
   - Shell script runnable via `curl -fsSL https://get.varistha.dev/install.sh | bash` or local execution.
   - Verifies system requirements: Python 3.12+, git, docker / docker compose.
   - Detects package managers (`uv`, `pipx`, `pip`).
   - Clones or updates Varistha repository to target install directory (default: `~/.varistha`).
   - Installs `varistha-cli` into user path.
   - Creates `deploy/.env` from `.env.example` if not already present.
   - Runs `varistha --help` to confirm successful installation.

2. **One-Line Windows PowerShell Installer (`scripts/install.ps1`)**:
   - PowerShell script runnable via `irm https://get.varistha.dev/install.ps1 | iex` or local execution.
   - Verifies system requirements: Python 3.12+, git, docker.
   - Clones or updates Varistha repository to `$HOME\.varistha`.
   - Installs CLI via `uv` or `pip`.
   - Creates `.env` and validates installation.

3. **Packaging Integrity & CLI Entrypoint**:
   - Verify `packages/cli/pyproject.toml` entrypoints and dependencies.
   - Ensure `varistha --version` outputs clear version information (`varistha 0.1.0`).

4. **Testing Suite (`packages/cli/tests/test_packaging_and_scripts.py`)**:
   - Test CLI version flag `--version` and help outputs for all subcommands.
   - Test `scripts/install.sh` for POSIX syntax validity (no bashisms breaking /bin/sh if standard POSIX, or explicit bash header).
   - Test `scripts/install.ps1` PowerShell script syntax and structure.

## Verification
- `python scripts/check_boundaries.py`
- `uv run ruff check .`
- `uv run pyright apps/api`
- `uv run pytest packages/cli/tests/test_packaging_and_scripts.py`
- Git commit & push with green GitHub Actions on both `master` and `main`.
