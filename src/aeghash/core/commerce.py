"""Commerce order orchestration with PV calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Mapping, Optional, Sequence

from aeghash.core.commerce_service import AegmallOrderPayload, AegmallOrderService
from aeghash.core.repositories import (
    OrderRecord,
    OrderRepository,
    ProductRecord,
    ProductRepository,
)


class CommerceError(ValueError):
    """Base error for commerce operations."""


class ProductUnavailableError(CommerceError):
    """Raised when a product cannot be purchased."""


class EmptyOrderError(CommerceError):
    """Raised when no order items are provided."""


@dataclass(slots=True)
class CreateOrderItem:
    """Order item payload."""

    product_id: str
    quantity: int


@dataclass(slots=True)
class CreateOrderRequest:
    """Order creation request."""

    user_id: str
    items: Sequence[CreateOrderItem]
    channel: str
    metadata: Optional[Mapping[str, object]] = None
    idempotency_key: Optional[str] = None
    sync_with_aegmall: bool = False


@dataclass(slots=True)
class OrderLineSummary:
    """Computed order line details."""

    product_id: str
    name: str
    quantity: int
    unit_price: Decimal
    unit_pv: Decimal
    line_amount: Decimal
    line_pv: Decimal


@dataclass(slots=True)
class CommerceOrderResult:
    """Outcome of an order creation request."""

    order: OrderRecord
    lines: Sequence[OrderLineSummary]
    aegmall_status: Optional[str]


class CommerceService:
    """Handles order creation and PV aggregation for the commerce module."""

    def __init__(
        self,
        product_repository: ProductRepository,
        order_repository: OrderRepository,
        *,
        id_factory: Optional[callable] = None,
        clock: Optional[callable] = None,
        aegmall_service: Optional[AegmallOrderService] = None,
    ) -> None:
        self._products = product_repository
        self._orders = order_repository
        self._id_factory = id_factory or (lambda: datetime.now(UTC).strftime("order-%Y%m%d%H%M%S%f"))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._aegmall = aegmall_service

    def create_order(self, request: CreateOrderRequest) -> CommerceOrderResult:
        if not request.items:
            raise EmptyOrderError("Order must contain at least one item.")

        lines = [self._build_line(item) for item in request.items]

        total_amount = sum((line.line_amount for line in lines), Decimal("0"))
        total_pv = sum((line.line_pv for line in lines), Decimal("0"))

        now = self._clock()
        order_id = str(self._id_factory())
        metadata = self._compose_metadata(lines, request.metadata)
        record = OrderRecord(
            order_id=order_id,
            user_id=request.user_id,
            total_amount=total_amount,
            pv_amount=total_pv,
            status="PAID",
            channel=request.channel,
            metadata=metadata,
            created_at=now,
        )

        persisted = self._orders.upsert_order(record)

        aegmall_status: Optional[str] = None
        if self._aegmall and request.sync_with_aegmall and request.idempotency_key:
            payload = AegmallOrderPayload(
                order_id=order_id,
                user_id=request.user_id,
                total_amount=total_amount,
                pv_amount=total_pv,
                channel=request.channel,
                metadata=metadata,
                idempotency_key=request.idempotency_key,
            )
            result = self._aegmall.process_order(payload)
            aegmall_status = result.status

        return CommerceOrderResult(order=persisted, lines=lines, aegmall_status=aegmall_status)

    def _build_line(self, item: CreateOrderItem) -> OrderLineSummary:
        if item.quantity <= 0:
            raise CommerceError("Quantity must be positive.")
        product = self._products.get_product(item.product_id)
        if product is None or product.status.lower() != "active":
            raise ProductUnavailableError(f"Product '{item.product_id}' is unavailable.")

        line_amount = (product.price * item.quantity).quantize(Decimal("0.0001"))
        line_pv = (product.pv * item.quantity).quantize(Decimal("0.0001"))
        return OrderLineSummary(
            product_id=product.product_id,
            name=product.name,
            quantity=item.quantity,
            unit_price=product.price,
            unit_pv=product.pv,
            line_amount=line_amount,
            line_pv=line_pv,
        )

    def _compose_metadata(
        self,
        lines: Sequence[OrderLineSummary],
        extra: Optional[Mapping[str, object]],
    ) -> Mapping[str, object]:
        line_payload = [
            {
                "product_id": line.product_id,
                "name": line.name,
                "quantity": line.quantity,
                "unit_price": str(line.unit_price),
                "unit_pv": str(line.unit_pv),
                "line_amount": str(line.line_amount),
                "line_pv": str(line.line_pv),
            }
            for line in lines
        ]
        base = {"lines": line_payload}
        if extra:
            base |= dict(extra)
        return base
