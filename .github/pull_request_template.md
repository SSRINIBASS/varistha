## Description

<!-- Describe the changes made in this pull request and the rationale. -->

## Bounded Context

- [ ] `registry/`
- [ ] `runtime/`
- [ ] `governance/`
- [ ] `observability/`
- [ ] `identity/`
- [ ] `plugins/`
- [ ] `ui/`
- [ ] `cli/`

## Phase Gate & Quality Checklist

- [ ] Tests added/updated covering changed code (&ge; 80% coverage per module).
- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass.
- [ ] `uv run pyright` passes with 0 errors/warnings.
- [ ] `python scripts/check_boundaries.py` passes with 0 violations.
- [ ] Any new dependencies use OSI-approved licenses (Apache-2.0, MIT, BSD) and are stated in description.
- [ ] Frontend changes adhere to semantic design tokens (zero hardcoded hex colors).
- [ ] Full automated test suite passes (`pytest` and `pnpm test`).
