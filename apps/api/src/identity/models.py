"""Identity domain models and role definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid


class Role(StrEnum):
    """User and API key authorization roles."""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


ROLE_HIERARCHY: dict[Role, int] = {
    Role.ADMIN: 3,
    Role.OPERATOR: 2,
    Role.VIEWER: 1,
}


@dataclass(frozen=True)
class Identity:
    """Authenticated caller identity."""

    id: uuid.UUID
    name: str
    role: Role
    api_key_id: uuid.UUID | None = None

    def has_role(self, minimum_role: Role) -> bool:
        """Check if caller's role meets or exceeds required role hierarchy level."""
        caller_level = ROLE_HIERARCHY.get(self.role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)
        return caller_level >= required_level
