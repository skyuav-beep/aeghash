"""Commerce pipeline utilities for processing AEGMALL orders."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Any, Callable, Mapping, Sequence

from aeghash.core.bonus_pipeline import BonusPipeline, OrderEvent
from aeghash.core.repositories import (
    BonusEntryRecord,
    IdempotencyKeyRecord,
    IdempotencyRepository,
    OrderRecord,
    OrderRepository,
)
from aeghash.utils import RetryConfig, retry


class IdempotencyConflictError(Exception):
    """Raised when an idempotency key is reused with a different payload."""


class IdempotencyInProgressError(Exception):
    """Raised when an idempotency key is currently being processed."""


@dataclass(slots=True)
class AegmallOrderPayload:
    """Inbound payload from AEGMALL commerce integration."""

    order_id: str
    user_id: str
    total_amount: Decimal
    pv_amount: Decimal
    channel: str
    metadata: Mapping[str, Any]
    idempotency_key: str


@dataclass(slots=True)
class OrderProcessingResult:
    """Outcome details for an ingested AEGMALL order."""

    order: OrderRecord
    bonuses: Sequence[BonusEntryRecord]
    status: str  # "created" or "duplicate"


class AegmallOrderService:
    """Coordinates PV persistence and bonus triggering with idempotency guarantees."""

    def __init__(
        self,
        *,
        order_repository: OrderRepository,
        idempotency_repository: IdempotencyRepository,
        bonus_pipeline: BonusPipeline | None = None,
        retry_config: RetryConfig | None = None,
        clock: Callable[[], datetime] | None = None,
        idempotency_scope: str = "aegmall",
        idempotency_ttl: timedelta | None = timedelta(days=1),
    ) -> None:
        self._orders = order_repository
        self._idempotency = idempotency_repository
        self._pipeline = bonus_pipeline
        self._retry_config = retry_config or RetryConfig()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._idempotency_scope = idempotency_scope
        self._idempotency_ttl = idempotency_ttl

    def process_order(self, payload: AegmallOrderPayload) -> OrderProcessingResult:
        """Persist order, compute PV bonuses, and uphold idempotency semantics."""
        now = self._clock()
        payload_hash = self._hash_payload(payload)
        scope = f"{self._idempotency_scope}:{payload.user_id}"

        expires_at = self._compute_expiry(now)
        record = IdempotencyKeyRecord(
            key=payload.idempotency_key,
            scope=scope,
            payload_hash=payload_hash,
            status="PENDING",
            created_at=now,
            expires_at=expires_at,
        )

        if not self._idempotency.create(record):
            existing = self._idempotency.get(key=payload.idempotency_key, scope=scope)
            if existing is None:
                raise IdempotencyInProgressError("Idempotency key is being initialised; retry later.")
            if existing.payload_hash != payload_hash:
                raise IdempotencyConflictError("Idempotency key reused with different payload.")
            if existing.status == "SUCCEEDED" and existing.resource_id:
                order = self._orders.get_order(existing.resource_id)
                if order is None:
                    raise IdempotencyInProgressError("Order not yet available; retry later.")
                return OrderProcessingResult(order=order, bonuses=(), status="duplicate")
            # Allow retry for failed or pending entries with identical payload.
            self._idempotency.mark_status(key=payload.idempotency_key, scope=scope, status="PENDING")

        try:
            order_record = self._orders.upsert_order(
                OrderRecord(
                    order_id=payload.order_id,
                    user_id=payload.user_id,
                    total_amount=payload.total_amount,
                    pv_amount=payload.pv_amount,
                    status="PAID",
                    channel=payload.channel,
                    metadata=dict(payload.metadata),
                    created_at=now,
                ),
            )

            bonuses: list[BonusEntryRecord] = []
            if self._pipeline:
                @retry(self._retry_config)
                def _run_pipeline() -> Sequence[BonusEntryRecord]:
                    order_event = OrderEvent(
                        order_id=payload.order_id,
                        user_id=payload.user_id,
                        pv_amount=payload.pv_amount,
                        total_amount=payload.total_amount,
                        metadata=dict(payload.metadata),
                    )
                    return self._pipeline.process_order(order_event)

                try:
                    bonuses = list(_run_pipeline())
                except ValueError:
                    bonuses = []

            self._idempotency.mark_status(
                key=payload.idempotency_key,
                scope=scope,
                status="SUCCEEDED",
                resource_id=order_record.order_id,
            )
            return OrderProcessingResult(order=order_record, bonuses=bonuses, status="created")
        except Exception:  # pragma: no cover - defensive rollback
            self._idempotency.mark_status(
                key=payload.idempotency_key,
                scope=scope,
                status="FAILED",
            )
            raise

    def _hash_payload(self, payload: AegmallOrderPayload) -> str:
        canonical = {
            "order_id": payload.order_id,
            "user_id": payload.user_id,
            "total_amount": str(payload.total_amount),
            "pv_amount": str(payload.pv_amount),
            "channel": payload.channel,
            "metadata": self._normalise_metadata(payload.metadata),
        }
        encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def _normalise_metadata(self, metadata: Mapping[str, Any]) -> Mapping[str, Any]:
        if isinstance(metadata, dict):
            return {str(key): metadata[key] for key in sorted(metadata)}
        return dict(metadata)

    def _compute_expiry(self, now: datetime) -> datetime | None:
        if self._idempotency_ttl is None:
            return None
        return now + self._idempotency_ttl
