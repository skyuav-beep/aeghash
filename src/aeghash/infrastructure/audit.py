"""Audit logging utilities for authentication events."""

from __future__ import annotations

from typing import Mapping, Optional

from aeghash.core.repositories import LoginAuditRecord
from aeghash.infrastructure.repositories import SqlAlchemyLoginAuditRepository
from aeghash.infrastructure.session import SessionManager


class LoginAuditLogger:
    """Persist authentication events for audit purposes."""

    def __init__(self, session_manager: SessionManager) -> None:
        self._session_manager = session_manager

    def handle_event(self, name: str, payload: Mapping[str, object]) -> None:
        status = self._map_status(name)
        if status is None:
            return

        provider = str(payload.get("provider", "unknown"))
        subject = self._extract_subject(status, payload)
        reason = self._extract_reason(status, payload)

        record = LoginAuditRecord(provider=provider, status=status, subject=subject, reason=reason)

        with self._session_manager.session_scope() as session:
            repository = SqlAlchemyLoginAuditRepository(session)
            repository.log(record)

    @staticmethod
    def _map_status(event_name: str) -> Optional[str]:
        if event_name == "auth.start":
            return "STARTED"
        if event_name == "auth.success":
            return "SUCCEEDED"
        if event_name == "auth.error":
            return "FAILED"
        if event_name == "two_factor.enabled":
            return "TWO_FACTOR_ENABLED"
        if event_name == "two_factor.disabled":
            return "TWO_FACTOR_DISABLED"
        return None

    @staticmethod
    def _extract_subject(status: str, payload: Mapping[str, object]) -> Optional[str]:
        subject = payload.get("subject")
        if status in {"SUCCEEDED", "TWO_FACTOR_ENABLED", "TWO_FACTOR_DISABLED"} and isinstance(subject, str):
            return subject
        return None

    @staticmethod
    def _extract_reason(status: str, payload: Mapping[str, object]) -> Optional[str]:
        reason = payload.get("reason")
        if status == "FAILED" and isinstance(reason, str):
            return reason
        if status == "TWO_FACTOR_DISABLED":
            actor_id = payload.get("actor_id")
            if isinstance(actor_id, str):
                return actor_id
        return None
