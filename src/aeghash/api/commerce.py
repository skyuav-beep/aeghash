"""AEGMALL inbound commerce API surface."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

from aeghash.core.commerce_service import (
    AegmallOrderPayload,
    AegmallOrderService,
    IdempotencyConflictError,
    IdempotencyInProgressError,
    OrderProcessingResult,
)
from aeghash.infrastructure.bootstrap import ServiceContainer, aegmall_order_service_scope


class AegmallOrderError(Exception):
    """Base error for AEGMALL order ingestion."""


class IdempotencyConflict(AegmallOrderError):
    """Raised when the provided idempotency key conflicts with an existing payload."""


class IdempotencyPending(AegmallOrderError):
    """Raised when an idempotency key is still being processed."""


@dataclass(slots=True)
class AegmallOrderRequest:
    """Normalized request payload for inbound AEGMALL orders."""

    order_id: str
    user_id: str
    total_amount: Decimal
    pv_amount: Decimal
    channel: str
    metadata: Mapping[str, Any]
    idempotency_key: str


@dataclass(slots=True)
class AegmallOrderResponse:
    """Result wrapper exposing processed order details."""

    status: str
    order_id: str
    bonuses_created: int
    bonus_ids: Sequence[str]


class AegmallInboundAPI:
    """Facade for handling inbound AEGMALL order events."""

    def __init__(self, container: ServiceContainer) -> None:
        self._container = container

    @classmethod
    def from_container(cls, container: ServiceContainer) -> "AegmallInboundAPI":
        return cls(container)

    def process_order(self, request: AegmallOrderRequest) -> AegmallOrderResponse:
        """Persist the order, trigger bonuses, and enforce idempotency."""
        payload = AegmallOrderPayload(
            order_id=request.order_id,
            user_id=request.user_id,
            total_amount=request.total_amount,
            pv_amount=request.pv_amount,
            channel=request.channel,
            metadata=dict(request.metadata),
            idempotency_key=request.idempotency_key,
        )
        with aegmall_order_service_scope(self._container.session_manager) as service:
            try:
                result = service.process_order(payload)
            except IdempotencyConflictError as exc:
                raise IdempotencyConflict(str(exc)) from exc
            except IdempotencyInProgressError as exc:
                raise IdempotencyPending(str(exc)) from exc

        return self._to_response(result)

    def _to_response(self, result: OrderProcessingResult) -> AegmallOrderResponse:
        bonus_ids = [entry.bonus_id for entry in result.bonuses]
        return AegmallOrderResponse(
            status=result.status,
            order_id=result.order.order_id,
            bonuses_created=len(bonus_ids),
            bonus_ids=bonus_ids,
        )
