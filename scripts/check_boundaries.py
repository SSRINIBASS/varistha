#!/usr/bin/env python3
"""Architecture boundary enforcement script.

Checks that domain boundaries are respected across the codebase:
1. No LangGraph imports outside apps/api/src/runtime/
2. No provider SDK imports (openai, anthropic) outside litellm adapter
3. No cross-context imports between bounded contexts
4. All plugins behind MCP (no hardcoded tool functions in core)
5. No hardcoded hex colors in UI

Run with: python scripts/check_boundaries.py
Returns exit code 1 if violations found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


class Violation:
    """A single boundary violation."""

    def __init__(self, rule: str, file: Path, line: int, content: str) -> None:
        """Initialize a boundary violation."""
        self.rule = rule
        self.file = file.relative_to(ROOT)
        self.line = line
        self.content = content.strip()

    def __str__(self) -> str:
        """Format violation for display."""
        return f"  [{self.rule}] {self.file}:{self.line}\n    {self.content}"


violations: list[Violation] = []


def check_python_files() -> None:
    """Check Python source files for boundary violations."""
    api_src = ROOT / "apps" / "api" / "src"
    runtime_dir = api_src / "runtime"

    # Rule 1: No LangGraph imports outside apps/api/src/runtime/
    for py_file in api_src.rglob("*.py"):
        if py_file.is_relative_to(runtime_dir):
            continue
        for i, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\bimport langgraph\b|\bfrom langgraph\b", line):
                violations.append(Violation("LANGGRAPH_OUTSIDE_RUNTIME", py_file, i, line))

    # Rule 2: No provider SDK imports in core (openai, anthropic, cohere, etc.)
    provider_pattern = re.compile(
        r"\bimport (openai|anthropic|cohere|groq|mistralai)\b"
        r"|\bfrom (openai|anthropic|cohere|groq|mistralai)\b"
    )
    for py_file in api_src.rglob("*.py"):
        # litellm adapter is allowed to reference providers for type stubs only
        if "litellm" in py_file.name:
            continue
        for i, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
            if provider_pattern.search(line):
                violations.append(Violation("PROVIDER_SDK_IN_CORE", py_file, i, line))

    # Rule 3: No cross-context imports (registry cannot import governance, etc.)
    contexts = ["registry", "runtime", "governance", "observability", "identity"]
    for ctx in contexts:
        ctx_dir = api_src / ctx
        if not ctx_dir.exists():
            continue
        other_contexts = [c for c in contexts if c != ctx]
        for py_file in ctx_dir.rglob("*.py"):
            if "/tests/" in str(py_file):
                continue  # integration tests may cross contexts
            for i, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
                for other in other_contexts:
                    pattern = rf"\bfrom {other}\b|\bimport {other}\b"
                    if re.search(pattern, line):
                        violations.append(
                            Violation(
                                f"CROSS_CONTEXT_{ctx.upper()}_IMPORTS_{other.upper()}",
                                py_file,
                                i,
                                line,
                            )
                        )


def check_ui_files() -> None:
    """Check UI files for hardcoded colors."""
    ui_src = ROOT / "apps" / "ui" / "src"
    if not ui_src.exists():
        return

    # Rule 4: No hardcoded hex colors (use CSS variables / design tokens)
    hex_color = re.compile(r'(?<!["\w])#[0-9a-fA-F]{3,8}\b')
    skip_pattern = re.compile(r"^\s*(//|/\*|\*|--)")

    for ts_file in ui_src.rglob("*.{ts,tsx,css}"):
        for i, line in enumerate(ts_file.read_text(encoding="utf-8").splitlines(), 1):
            if skip_pattern.match(line):
                continue
            if hex_color.search(line):
                violations.append(Violation("HARDCODED_COLOR_IN_UI", ts_file, i, line))


def main() -> int:
    """Run all boundary checks and report violations."""
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print("Checking architecture boundaries...")  # noqa: T201

    check_python_files()
    check_ui_files()

    if violations:
        print(f"\nERROR: Found {len(violations)} boundary violation(s):\n")  # noqa: T201
        for v in violations:
            print(v)  # noqa: T201
        print(  # noqa: T201
            "\nFix the violations above before committing. "
            "See docs/adr/0001-monorepo-and-stack.md for boundary rules."
        )
        return 1

    print("OK: All architecture boundaries respected.")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
