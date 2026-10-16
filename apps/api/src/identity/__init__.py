"""Identity bounded context package."""

from __future__ import annotations

from identity.dependencies import get_current_identity, require_role
from identity.models import Identity, Role
from identity.router import router
from identity.secrets_service import delete_secret, list_secrets, resolve_secret, store_secret

__all__ = [
    "Identity",
    "Role",
    "delete_secret",
    "get_current_identity",
    "list_secrets",
    "require_role",
    "resolve_secret",
    "router",
    "store_secret",
]
