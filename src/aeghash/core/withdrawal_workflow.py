"""Workflow orchestration for approving or rejecting withdrawal requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Mapping, Optional, Sequence

from aeghash.core.point_wallet import (
    PointWalletService,
    WithdrawalSnapshot,
    WITHDRAWAL_STATUS_APPROVED_STAGE1,
    WITHDRAWAL_STATUS_PENDING,
)
from aeghash.core.mining_workflow import MiningWithdrawalOrchestrator, WithdrawalExecutionError
from aeghash.security.risk import RiskRejected, RiskService, WithdrawalRiskContext
from aeghash.core.repositories import WithdrawalAuditRecord, WithdrawalAuditRepository


@dataclass(slots=True)
class WithdrawalEvent:
    """Notification payload emitted when workflow actions occur."""

    request_id: str
    wallet_id: str
    action: str
    actor_id: str
    amount: Decimal
    status: str
    notes: Optional[str]
    created_at: datetime


class WithdrawalWorkflowService:
    """High-level workflow service coordinating withdrawals and audit logging."""

    def __init__(
        self,
        wallet_service: PointWalletService,
        audit_repository: WithdrawalAuditRepository,
        *,
        clock: callable | None = None,
        event_listeners: Sequence[callable[[WithdrawalEvent], None]] | None = None,
        risk_service: RiskService | None = None,
        mining_orchestrator: MiningWithdrawalOrchestrator | None = None,
        two_step_required: bool = False,
        distinct_approvers: bool = True,
    ) -> None:
        self._wallet_service = wallet_service
        self._audit_repository = audit_repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._listeners = list(event_listeners or [])
        self._risk_service = risk_service
        self._mining_orchestrator = mining_orchestrator
        self._two_step_required = two_step_required
        self._distinct_approvers = distinct_approvers

    def request_withdrawal(
        self,
        *,
        wallet_id: str,
        amount: Decimal,
        requested_by: str,
        reference_id: Optional[str] = None,
        metadata: Optional[Mapping[str, object]] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_id: Optional[str] = None,
        geo_location: Optional[str] = None,
    ) -> WithdrawalSnapshot:
        snapshot = self._wallet_service.request_withdrawal(
            wallet_id=wallet_id,
            amount=amount,
            requested_by=requested_by,
            reference_id=reference_id,
            metadata=metadata,
        )

        self._log(snapshot, actor_id=requested_by, action="requested", notes=notes, metadata=metadata)

        if self._risk_service:
            context = WithdrawalRiskContext(
                request_id=snapshot.request_id,
                user_id=requested_by,
                amount=amount,
                ip_address=ip_address,
                device_id=device_id,
                geo_location=geo_location,
            )
            try:
                decision = self._risk_service.evaluate_withdrawal(context)
            except RiskRejected as exc:
                cancelled = self._wallet_service.cancel_withdrawal(
                    snapshot.request_id,
                    cancelled_by="risk-system",
                )
                self._log(
                    cancelled,
                    actor_id="risk-system",
                    action="cancelled",
                    notes=f"Auto-cancelled due to risk: {exc}",
                    metadata={"reason": str(exc)},
                )
                raise
            else:
                if decision.requires_review:
                    self._log(
                        snapshot,
                        actor_id="risk-system",
                        action="flagged",
                        notes="Risk review required",
                        metadata={
                            "findings": [finding.message for finding in decision.findings],
                        },
                    )
        return snapshot

    def approve(
        self,
        request_id: str,
        *,
        approved_by: str,
        notes: Optional[str] = None,
        coin: Optional[str] = None,
        finalize: bool = True,
    ) -> WithdrawalSnapshot:
        pending = self._wallet_service.get_withdrawal(request_id)
        if not self._two_step_required:
            finalize = True

        if self._two_step_required and pending.status == WITHDRAWAL_STATUS_PENDING:
            if not finalize:
                metadata = {"stage": "stage1"}
                snapshot = self._wallet_service.mark_stage1_approval(
                    request_id,
                    approver_id=approved_by,
                    notes=notes,
                    metadata=metadata,
                )
                self._log(snapshot, actor_id=approved_by, action="approved_stage1", notes=notes, metadata=metadata)
                return snapshot
            raise WithdrawalExecutionError("Second approval required; finalize flag must be False on first approval.")

        if self._two_step_required and pending.status == WITHDRAWAL_STATUS_APPROVED_STAGE1:
            stage1_approver = (pending.metadata or {}).get("stage1_approver")
            if self._distinct_approvers and stage1_approver == approved_by:
                raise WithdrawalExecutionError("Second approval must be performed by a different reviewer.")
            finalize = True

        if not finalize:
            raise WithdrawalExecutionError("Finalize flag must be True when completing the approval.")

        snapshot = self._wallet_service.approve_withdrawal(request_id, approved_by=approved_by, notes=notes)
        metadata = None

        if self._should_execute_mining(snapshot, coin):
            if not self._mining_orchestrator:
                raise WithdrawalExecutionError("Mining orchestrator not configured for mining withdrawal.")
            try:
                outcome = self._mining_orchestrator.approve_and_execute(
                    request_id,
                    approved_by=approved_by,
                    notes=notes,
                    coin=coin,
                )
            except WithdrawalExecutionError as exc:
                failure_snapshot = self._wallet_service.get_withdrawal(request_id)
                self._log(
                    failure_snapshot,
                    actor_id=approved_by,
                    action="failed",
                    notes=str(exc),
                    metadata={"error": str(exc)},
                )
                raise
            else:
                metadata = {
                    "hashdam_withdraw_id": outcome.mining_request.withdraw_id,
                    "coin": outcome.mining_request.coin,
                }
                snapshot = self._wallet_service.annotate_withdrawal(request_id, metadata)

        if self._two_step_required:
            metadata = dict(snapshot.metadata or {})
            metadata.setdefault("stage", "final")
        self._log(snapshot, actor_id=approved_by, action="approved", notes=notes, metadata=metadata)
        return snapshot

    def reject(
        self,
        request_id: str,
        *,
        rejected_by: str,
        notes: Optional[str] = None,
    ) -> WithdrawalSnapshot:
        snapshot = self._wallet_service.reject_withdrawal(request_id, rejected_by=rejected_by, notes=notes)
        self._log(snapshot, actor_id=rejected_by, action="rejected", notes=notes)
        return snapshot

    def cancel(
        self,
        request_id: str,
        *,
        cancelled_by: str,
        notes: Optional[str] = None,
    ) -> WithdrawalSnapshot:
        snapshot = self._wallet_service.cancel_withdrawal(request_id, cancelled_by=cancelled_by)
        self._log(snapshot, actor_id=cancelled_by, action="cancelled", notes=notes)
        return snapshot

    def list_audit_trail(self, request_id: str, *, limit: int = 100) -> Sequence[WithdrawalAuditRecord]:
        return self._audit_repository.list_for_request(request_id, limit=limit)

    def add_listener(self, listener: callable[[WithdrawalEvent], None]) -> None:
        self._listeners.append(listener)

    # ------------------------------------------------------------------ helpers

    def _log(
        self,
        snapshot: WithdrawalSnapshot,
        *,
        actor_id: str,
        action: str,
        notes: Optional[str],
        metadata: Optional[Mapping[str, object]] = None,
    ) -> None:
        timestamp = self._clock()
        record = WithdrawalAuditRecord(
            request_id=snapshot.request_id,
            wallet_id=snapshot.wallet_id,
            action=action,
            actor_id=actor_id,
            amount=snapshot.amount,
            status=snapshot.status,
            notes=notes,
            metadata=metadata,
            created_at=timestamp,
        )
        self._audit_repository.log(record)
        event = WithdrawalEvent(
            request_id=record.request_id,
            wallet_id=record.wallet_id,
            action=record.action,
            actor_id=record.actor_id,
            amount=record.amount,
            status=record.status,
            notes=record.notes,
            created_at=record.created_at,
        )
        for listener in self._listeners:
            listener(event)

    def _should_execute_mining(self, snapshot: WithdrawalSnapshot, coin_override: Optional[str]) -> bool:
        if not self._mining_orchestrator:
            return False
        metadata = snapshot.metadata or {}
        if coin_override:
            return True
        return metadata.get("coin") is not None or metadata.get("provider") == "hashdam"
