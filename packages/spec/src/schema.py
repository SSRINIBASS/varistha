"""JSON Schema generation for the Varistha Agent Spec.

Generates a JSON Schema from the Pydantic ``AgentSpec`` model and writes
it to ``schema.json`` next to this file.  The schema is committed to the
repository so editors (VS Code, Cursor, etc.) can provide inline validation
when editing ``*.yaml`` agent specs.

Usage::

    python -m schema       # generates packages/spec/src/schema.json
    from schema import generate_json_schema  # import programmatically
"""

from __future__ import annotations

import json
from pathlib import Path

from models import AgentSpec

_SCHEMA_PATH = Path(__file__).parent / "schema.json"


def generate_json_schema() -> dict:  # type: ignore[type-arg]
    """Return the JSON Schema dict for ``AgentSpec``."""
    return AgentSpec.model_json_schema()


def write_schema(path: Path = _SCHEMA_PATH) -> None:
    """Write the JSON Schema to *path* (default: ``schema.json`` next to this file)."""
    schema = generate_json_schema()
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys

    write_schema()
    print(f"Schema written to {_SCHEMA_PATH}")  # noqa: T201
    sys.exit(0)
