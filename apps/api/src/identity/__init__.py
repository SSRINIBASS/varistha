"""Identity bounded context package."""

from __future__ import annotations

from identity.dependencies import get_current_identity, require_role
from identity.models import Identity, Role
from identity.router import router

__all__ = [
    "Identity",
    "Role",
    "get_current_identity",
    "require_role",
    "router",
]
