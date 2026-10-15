"""Validator entry point for Varistha agent specs.

Accepts a raw dict (typically parsed from YAML or JSON) and returns a
validated ``AgentSpec`` instance, or raises ``SpecValidationError`` with
human-readable error messages.

Usage::

    import yaml
    from spec.validator import validate_spec

    with open("agent.yaml") as fh:
        raw = yaml.safe_load(fh)

    agent = validate_spec(raw)   # raises SpecValidationError on bad input
"""

from __future__ import annotations

from typing import Any

from exceptions import SpecValidationError
from models import AgentSpec
from pydantic import ValidationError


def validate_spec(raw: dict[str, Any]) -> AgentSpec:
    """Parse and validate a raw dict into a typed ``AgentSpec``.

    Args:
        raw: The raw spec data, typically loaded from YAML or JSON.

    Returns:
        A fully validated ``AgentSpec`` instance.

    Raises:
        SpecValidationError: If any validation rule is violated.  The
            exception's ``errors`` attribute contains one human-readable
            string per violation.

    """
    try:
        return AgentSpec.model_validate(raw)
    except ValidationError as exc:
        messages: list[str] = []
        for err in exc.errors():
            loc = " -> ".join(str(part) for part in err["loc"]) if err["loc"] else "spec"
            messages.append(f"{loc}: {err['msg']}")
        raise SpecValidationError(messages) from exc


def validate_spec_yaml(yaml_text: str) -> AgentSpec:
    """Parse a YAML string and validate it as an ``AgentSpec``.

    Args:
        yaml_text: Raw YAML content of the agent spec file.

    Returns:
        A fully validated ``AgentSpec`` instance.

    Raises:
        SpecValidationError: If YAML is malformed or validation fails.

    """
    import yaml

    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise SpecValidationError([f"YAML parse error: {exc}"]) from exc

    if not isinstance(raw, dict):
        raise SpecValidationError(["Spec must be a YAML mapping, not a scalar or list."])

    return validate_spec(raw)
