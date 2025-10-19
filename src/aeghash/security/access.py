"""Access policy helpers for enforcing admin RLS and masking rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Set

from aeghash.core.repositories import SessionRecord
from aeghash.security.permissions import PermissionService


def _extract_base_roles(raw_roles: Sequence[str]) -> tuple[str, ...]:
    return tuple(role for role in raw_roles if not role.startswith("scope:"))


def _extract_scopes(raw_roles: Sequence[str]) -> Mapping[str, Set[str]]:
    scopes: dict[str, Set[str]] = {}
    for entry in raw_roles:
        if not entry.startswith("scope:"):
            continue
        parts = entry.split(":")
        if len(parts) < 3:
            continue
        domain = parts[1]
        value = ":".join(parts[2:])
        scopes.setdefault(domain, set()).add(value)
    return scopes


@dataclass(slots=True)
class AccessContext:
    """Normalized view of a session record for downstream access control."""

    user_id: str
    raw_roles: tuple[str, ...]
    roles: tuple[str, ...]
    permissions: Set[str]
    scopes: Mapping[str, Set[str]]

    @classmethod
    def from_session(
        cls,
        session: SessionRecord,
        *,
        permission_service: PermissionService | None = None,
    ) -> "AccessContext":
        service = permission_service or PermissionService()
        base_roles = _extract_base_roles(session.roles)
        permissions = service.permissions_for(base_roles)
        scopes = _extract_scopes(session.roles)
        return cls(
            user_id=session.user_id,
            raw_roles=tuple(session.roles),
            roles=base_roles,
            permissions=permissions,
            scopes=scopes,
        )


@dataclass(slots=True)
class AccessPolicy:
    """Derive fine-grained access decisions from an access context."""

    context: AccessContext

    def has(self, permission: str) -> bool:
        return permission in self.context.permissions

    def has_all(self, permissions: Iterable[str]) -> bool:
        return all(self.has(permission) for permission in permissions)

    # ------------------------------------------------------------------ masking helpers

    def can_view_full_personal_data(self) -> bool:
        return self.has("personal_data:view_full") or self.has("wallets:view_sensitive")

    def can_view_full_audit_subjects(self) -> bool:
        return self.has("audits:view_full") or self.can_view_full_personal_data()

    # ------------------------------------------------------------------ KPI scope helpers

    def has_global_kpi_access(self) -> bool:
        return self.has("kpi:read_all") or self.has("organizations:view_all")

    def allowed_kpi_nodes(self) -> Mapping[str | None, Set[str]]:
        raw = self.context.scopes.get("kpi", set())
        scoped: dict[str | None, Set[str]] = {}
        for entry in raw:
            parts = entry.split(":")
            if not parts:
                continue
            if parts[0] != "node":
                continue
            if len(parts) == 2:
                tree_type: str | None = None
                node_id = parts[1]
            else:
                tree_type = parts[1] or None
                node_id = ":".join(parts[2:])
            scoped.setdefault(tree_type, set()).add(node_id)
        return scoped
