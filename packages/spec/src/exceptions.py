"""Exceptions raised by the Varistha spec validator."""

from __future__ import annotations


class SpecValidationError(Exception):
    """Raised when an agent spec fails validation.

    Wraps one or more Pydantic validation errors into human-readable messages
    so callers (CLI, API) can surface them without depending on Pydantic internals.
    """

    def __init__(self, errors: list[str]) -> None:
        """Initialise with a list of human-readable error strings."""
        self.errors = errors
        joined = "\n".join(f"  - {e}" for e in errors)
        super().__init__(f"Agent spec validation failed:\n{joined}")
