"""Role and permission utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Set


ROLE_MATRIX: Mapping[str, Set[str]] = {
    "admin": {
        "dashboard:view",
        "users:manage",
        "users:two_factor:view",
        "users:two_factor:disable",
        "wallets:approve_withdrawal",
        "wallets:view_sensitive",
        "audits:view",
        "audits:view_full",
        "roles:assign",
        "organizations:view",
        "organizations:view_all",
        "kpi:read",
        "kpi:read_all",
        "personal_data:view_full",
    },
    "finance": {
        "dashboard:view",
        "wallets:approve_withdrawal",
        "wallets:view_transactions",
        "wallets:view_sensitive",
        "audits:view",
        "organizations:view",
        "kpi:read",
        "personal_data:view_full",
    },
    "support": {
        "dashboard:view",
        "users:view",
        "users:two_factor:view",
        "audits:view",
        "organizations:view",
        "kpi:read",
    },
    "member": {"dashboard:view", "wallets:view"},
}


@dataclass(slots=True)
class AuthorizationDecision:
    allowed: bool
    missing_permissions: Set[str]


class PermissionService:
    """Evaluate permissions for roles based on the predefined matrix."""

    def __init__(self, role_matrix: Mapping[str, Iterable[str]] | None = None) -> None:
        self._matrix: Dict[str, Set[str]] = {
            role: set(permissions) for role, permissions in (role_matrix or ROLE_MATRIX).items()
        }

    def permissions_for(self, roles: Iterable[str]) -> Set[str]:
        permissions: Set[str] = set()
        for role in roles:
            permissions.update(self._matrix.get(role, set()))
        return permissions

    def authorize(self, roles: Iterable[str], required_permissions: Iterable[str]) -> AuthorizationDecision:
        available = self.permissions_for(roles)
        required = set(required_permissions)
        missing = required - available
        return AuthorizationDecision(allowed=not missing, missing_permissions=missing)
