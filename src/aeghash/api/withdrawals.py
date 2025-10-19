"""Administrative APIs for managing withdrawal approvals."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, Sequence

from aeghash.core.mining_workflow import WithdrawalExecutionError
from aeghash.core.point_wallet import InvalidWithdrawalState, WithdrawalNotFound, WithdrawalSnapshot
from aeghash.core.withdrawal_workflow import WithdrawalWorkflowService
from aeghash.infrastructure.bootstrap import ServiceContainer, withdrawal_workflow_scope


class WithdrawalApprovalAPI:
    """Facade wrapping WithdrawalWorkflowService for admin operations."""

    def __init__(self, container: ServiceContainer) -> None:
        self._container = container

    @classmethod
    def from_container(cls, container: ServiceContainer) -> "WithdrawalApprovalAPI":
        return cls(container)

    def approve(
        self,
        request_id: str,
        *,
        approved_by: str,
        notes: str | None = None,
        coin: str | None = None,
        finalize: bool = True,
    ) -> WithdrawalSnapshot:
        if not self._container.hashdam_client_factory:
            raise RuntimeError("HashDam client factory is not configured.")
        with withdrawal_workflow_scope(
            self._container.session_manager,
            mining_client_factory=self._container.hashdam_client_factory,
            notifier=self._container.notifier,
        ) as workflow:
            try:
                return workflow.approve(
                    request_id,
                    approved_by=approved_by,
                    notes=notes,
                    coin=coin,
                    finalize=finalize,
                )
            except WithdrawalNotFound:
                raise
            except InvalidWithdrawalState:
                raise
            except WithdrawalExecutionError:
                raise

    def list_audit_events(self, request_id: str) -> Sequence[Mapping[str, Any]]:
        if not self._container.hashdam_client_factory:
            raise RuntimeError("HashDam client factory is not configured.")
        with withdrawal_workflow_scope(
            self._container.session_manager,
            mining_client_factory=self._container.hashdam_client_factory,
            notifier=self._container.notifier,
        ) as workflow:
            records = workflow.list_audit_trail(request_id)
            return [self._serialize_audit_record(record) for record in records]

    def _serialize_audit_record(self, record) -> Mapping[str, Any]:
        payload = asdict(record)
        return payload
