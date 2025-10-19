from datetime import UTC, datetime
from decimal import Decimal

import pytest

from aeghash.core.commerce import (
    CommerceError,
    CommerceService,
    CreateOrderItem,
    CreateOrderRequest,
    EmptyOrderError,
    ProductUnavailableError,
)
from aeghash.core.commerce_service import OrderProcessingResult
from aeghash.core.repositories import OrderRecord, ProductRecord
from aeghash.utils import (
    InMemoryOrderRepository,
    InMemoryProductRepository,
)


class StubAegmallService:
    def __init__(self) -> None:
        self.payloads = []

    def process_order(self, payload):
        self.payloads.append(payload)
        dummy_order = OrderRecord(
            order_id=payload.order_id,
            user_id=payload.user_id,
            total_amount=payload.total_amount,
            pv_amount=payload.pv_amount,
            status="PAID",
            channel=payload.channel,
            metadata=payload.metadata,
            created_at=datetime.now(UTC),
        )
        return OrderProcessingResult(order=dummy_order, bonuses=[], status="created")


@pytest.fixture()
def product_repo() -> InMemoryProductRepository:
    repo = InMemoryProductRepository()
    now = datetime.now(UTC)
    repo.products["prod-1"] = ProductRecord(
        product_id="prod-1",
        name="Hashpower 100",
        price=Decimal("200.00"),
        pv=Decimal("120"),
        status="active",
        metadata={},
        updated_at=now,
    )
    repo.products["prod-2"] = ProductRecord(
        product_id="prod-2",
        name="Hashpower 50",
        price=Decimal("120.00"),
        pv=Decimal("60"),
        status="active",
        metadata={},
        updated_at=now,
    )
    return repo


def test_create_order_calculates_totals(product_repo: InMemoryProductRepository) -> None:
    order_repo = InMemoryOrderRepository()
    service = CommerceService(product_repo, order_repo, clock=lambda: datetime(2025, 1, 1, tzinfo=UTC))

    request = CreateOrderRequest(
        user_id="user-1",
        items=[
            CreateOrderItem(product_id="prod-1", quantity=1),
            CreateOrderItem(product_id="prod-2", quantity=2),
        ],
        channel="ONLINE",
    )

    result = service.create_order(request)

    assert result.order.total_amount == Decimal("440.00")
    assert result.order.pv_amount == Decimal("240.00")
    assert len(result.lines) == 2
    assert order_repo.get_order(result.order.order_id) is not None


def test_create_order_requires_items(product_repo: InMemoryProductRepository) -> None:
    service = CommerceService(product_repo, InMemoryOrderRepository())
    request = CreateOrderRequest(user_id="user-1", items=[], channel="ONLINE")
    with pytest.raises(EmptyOrderError):
        service.create_order(request)


def test_create_order_rejects_inactive_product(product_repo: InMemoryProductRepository) -> None:
    product_repo.products["prod-1"].status = "inactive"
    service = CommerceService(product_repo, InMemoryOrderRepository())
    request = CreateOrderRequest(user_id="user-1", items=[CreateOrderItem("prod-1", 1)], channel="ONLINE")
    with pytest.raises(ProductUnavailableError):
        service.create_order(request)


def test_create_order_syncs_with_aegmall(product_repo: InMemoryProductRepository) -> None:
    order_repo = InMemoryOrderRepository()
    stub_aegmall = StubAegmallService()
    service = CommerceService(
        product_repo,
        order_repo,
        aegmall_service=stub_aegmall,
        clock=lambda: datetime(2025, 1, 1, tzinfo=UTC),
    )

    request = CreateOrderRequest(
        user_id="user-1",
        items=[CreateOrderItem("prod-1", 1)],
        channel="ONLINE",
        idempotency_key="idem-1",
        sync_with_aegmall=True,
    )

    result = service.create_order(request)
    assert result.aegmall_status == "created"
    assert stub_aegmall.payloads
