"""Risk detection helpers for withdrawal workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable, Mapping, Optional, Protocol, Sequence

from aeghash.core.repositories import KnownDeviceRecord, RiskEventRecord, RiskRepository
from aeghash.utils import NotificationMessage, Notifier


class RiskRejected(RuntimeError):
    """Raised when a risk rule blocks the requested action."""


@dataclass(slots=True)
class WithdrawalRiskContext:
    """Context supplied to risk evaluators for withdrawal operations."""

    request_id: str
    user_id: str
    amount: Decimal
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    geo_location: Optional[str] = None


@dataclass(slots=True)
class RiskFinding:
    """Single rule evaluation result."""

    rule: str
    severity: str
    message: str
    metadata: Mapping[str, object] | None = None


@dataclass(slots=True)
class RiskDecision:
    """Aggregated decision returned by the evaluator."""

    allowed: bool
    findings: Sequence[RiskFinding] = field(default_factory=tuple)

    @property
    def requires_review(self) -> bool:
        return any(finding.severity in {"review", "high"} for finding in self.findings)

    @property
    def blocked(self) -> bool:
        return not self.allowed


class RiskRule(Protocol):
    """Interface implemented by individual risk rules."""

    def evaluate(self, context: WithdrawalRiskContext, repository: RiskRepository) -> Optional[RiskFinding]:
        ...


@dataclass(slots=True)
class AmountLimitRule:
    warn_limit: Decimal
    block_limit: Decimal

    def evaluate(self, context: WithdrawalRiskContext, repository: RiskRepository) -> Optional[RiskFinding]:  # noqa: ARG002
        amount = context.amount
        if amount >= self.block_limit:
            return RiskFinding(
                rule="amount_limit",
                severity="block",
                message=f"Withdrawal amount {amount} exceeds hard limit {self.block_limit}",
            )
        if amount >= self.warn_limit:
            return RiskFinding(
                rule="amount_limit",
                severity="review",
                message=f"Withdrawal amount {amount} exceeds review limit {self.warn_limit}",
            )
        return None


@dataclass(slots=True)
class IpReputationRule:
    blocked_ips: Sequence[str] = ()
    trusted_ips: Sequence[str] = ()

    def evaluate(self, context: WithdrawalRiskContext, repository: RiskRepository) -> Optional[RiskFinding]:  # noqa: ARG002
        ip = context.ip_address
        if not ip:
            return None
        if ip in self.blocked_ips:
            return RiskFinding(
                rule="ip_reputation",
                severity="block",
                message="IP address is blocked",
                metadata={"ip": ip},
            )
        if self.trusted_ips and ip not in self.trusted_ips:
            return RiskFinding(
                rule="ip_reputation",
                severity="review",
                message="Withdrawal from untrusted IP",
                metadata={"ip": ip},
            )
        return None


@dataclass(slots=True)
class DeviceNoveltyRule:
    review_limit: Decimal

    def evaluate(self, context: WithdrawalRiskContext, repository: RiskRepository) -> Optional[RiskFinding]:
        device_id = context.device_id
        if not device_id:
            return None
        record = repository.get_known_device(context.user_id, device_id)
        now = datetime.now(UTC)
        if record is None:
            repository.upsert_known_device(
                KnownDeviceRecord(
                    user_id=context.user_id,
                    device_id=device_id,
                    first_seen=now,
                    last_seen=now,
                ),
            )
            if context.amount >= self.review_limit:
                return RiskFinding(
                    rule="device_novelty",
                    severity="review",
                    message="High-value withdrawal from new device",
                    metadata={"device_id": device_id},
                )
            return None

        repository.upsert_known_device(
            KnownDeviceRecord(
                user_id=record.user_id,
                device_id=record.device_id,
                first_seen=record.first_seen,
                last_seen=now,
            ),
        )
        return None


@dataclass(slots=True)
class RiskConfig:
    amount_rule: AmountLimitRule
    ip_rule: Optional[IpReputationRule] = None
    device_rule: Optional[DeviceNoveltyRule] = None


class RiskService:
    """Evaluate withdrawal risk and persist audit trails."""

    def __init__(
        self,
        repository: RiskRepository,
        config: RiskConfig,
        *,
        notifier: Notifier | None = None,
        event_id_factory: callable | None = None,
        clock: callable | None = None,
    ) -> None:
        self._repository = repository
        self._config = config
        self._notifier = notifier
        self._event_id_factory = event_id_factory or (lambda: datetime.now(UTC).strftime("%Y%m%d%H%M%S%f"))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._rules: list[RiskRule] = [config.amount_rule]
        if config.ip_rule:
            self._rules.append(config.ip_rule)
        if config.device_rule:
            self._rules.append(config.device_rule)

    def evaluate_withdrawal(self, context: WithdrawalRiskContext) -> RiskDecision:
        findings: list[RiskFinding] = []
        for rule in self._rules:
            finding = rule.evaluate(context, self._repository)
            if finding:
                findings.append(finding)

        decision = self._build_decision(findings)
        self._record_events(context, decision)
        self._notify(context, decision)

        if decision.blocked:
            raise RiskRejected(
                ". ".join(f"{finding.rule}: {finding.message}" for finding in findings if finding.severity == "block"),
            )
        return decision

    def _build_decision(self, findings: Iterable[RiskFinding]) -> RiskDecision:
        findings = list(findings)
        allowed = not any(finding.severity == "block" for finding in findings)
        return RiskDecision(allowed=allowed, findings=findings)

    def _record_events(self, context: WithdrawalRiskContext, decision: RiskDecision) -> None:
        for finding in decision.findings:
            event = RiskEventRecord(
                event_id=self._event_id_factory(),
                user_id=context.user_id,
                category=finding.rule,
                severity=finding.severity,
                message=finding.message,
                attributes={
                    "request_id": context.request_id,
                    "amount": str(context.amount),
                    "ip": context.ip_address,
                    "device_id": context.device_id,
                    "geo": context.geo_location,
                    **(finding.metadata or {}),
                },
                created_at=self._clock(),
            )
            self._repository.record_event(event)

    def _notify(self, context: WithdrawalRiskContext, decision: RiskDecision) -> None:
        if not self._notifier:
            return
        for finding in decision.findings:
            if finding.severity in {"review", "block"}:
                body = (
                    f"Rule: {finding.rule}\n"
                    f"Severity: {finding.severity}\n"
                    f"User: {context.user_id}\n"
                    f"Amount: {context.amount}\n"
                    f"IP: {context.ip_address}\n"
                    f"Device: {context.device_id}\n"
                    f"Details: {finding.message}"
                )
                self._notifier.send(
                    NotificationMessage(
                        subject=f"Withdrawal risk detected ({finding.severity})",
                        body=body,
                    ),
                )
