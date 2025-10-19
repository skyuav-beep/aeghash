"""API helpers for login audit queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from sqlalchemy.orm import Session

from aeghash.core.repositories import LoginAuditRecord, LoginAuditRepository
from aeghash.infrastructure.bootstrap import ServiceContainer
from aeghash.infrastructure.repositories import SqlAlchemyLoginAuditRepository


@dataclass(slots=True)
class LoginAuditQuery:
    limit: int = 100


class LoginAuditAPI:
    def __init__(self, container: ServiceContainer, factory: Callable[[Session], LoginAuditRepository]) -> None:
        self._container = container
        self._factory = factory

    def list_recent(self, *, limit: int = 100) -> Sequence[LoginAuditRecord]:
        with self._container.session_manager.session_scope() as session:
            repo = self._factory(session)
            return repo.list_recent(limit=limit)

    @classmethod
    def from_container(cls, container: ServiceContainer) -> "LoginAuditAPI":
        return cls(container, factory=lambda session: SqlAlchemyLoginAuditRepository(session))


__all__ = ["LoginAuditAPI", "LoginAuditQuery"]
