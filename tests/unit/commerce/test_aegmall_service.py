from datetime import UTC, datetime
from decimal import Decimal

import pytest

from aeghash.core.bonus_pipeline import OrderEvent
from aeghash.core.commerce_service import (
    AegmallOrderPayload,
    AegmallOrderService,
    IdempotencyConflictError,
)
from aeghash.core.repositories import BonusEntryRecord, OrderRecord
from aeghash.utils import (
    InMemoryIdempotencyRepository,
    InMemoryOrderRepository,
    RetryConfig,
)


class StubBonusPipeline:
    def __init__(self, responses: list[BonusEntryRecord]) -> None:
        self._responses = responses
        self.calls: list[OrderEvent] = []

    def process_order(self, event: OrderEvent):
        self.calls.append(event)
        return list(self._responses)


class FlakyBonusPipeline(StubBonusPipeline):
    def __init__(self, responses: list[BonusEntryRecord], failures: int) -> None:
        super().__init__(responses)
        self.failures = failures

    def process_order(self, event: OrderEvent):
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("transient failure")
        return super().process_order(event)


class FailingBonusPipeline(StubBonusPipeline):
    def process_order(self, event: OrderEvent):
        raise RuntimeError("permanent failure")


@pytest.fixture()
def clock_now() -> datetime:
    return datetime(2025, 1, 1, 12, 0, tzinfo=UTC)


def sample_bonus(order_id: str, created_at: datetime) -> BonusEntryRecord:
    return BonusEntryRecord(
        bonus_id="bonus-1",
        user_id="root",
        source_user_id="root",
        bonus_type="recommend",
        level=1,
        bonus_amount=Decimal("10"),
        status="PENDING",
        metadata={"order_id": order_id, "pv_amount": "100"},
        created_at=created_at,
        order_id=order_id,
        pv_amount=Decimal("100"),
    )


def test_process_order_persists_order_and_bonuses(clock_now: datetime) -> None:
    orders = InMemoryOrderRepository()
    idempotency = InMemoryIdempotencyRepository()
    pipeline = StubBonusPipeline([sample_bonus("order-1", clock_now)])
    service = AegmallOrderService(
        order_repository=orders,
        idempotency_repository=idempotency,
        bonus_pipeline=pipeline,
        retry_config=RetryConfig(attempts=1),
        clock=lambda: clock_now,
    )

    payload = AegmallOrderPayload(
        order_id="order-1",
        user_id="user-1",
        total_amount=Decimal("200"),
        pv_amount=Decimal("100"),
        channel="ONLINE",
        metadata={"source": "test"},
        idempotency_key="idem-1",
    )

    result = service.process_order(payload)

    assert result.status == "created"
    assert isinstance(result.order, OrderRecord)
    assert orders.get_order("order-1") is not None
    record = idempotency.get(key="idem-1", scope="aegmall:user-1")
    assert record is not None
    assert record.status == "SUCCEEDED"
    assert result.bonuses and result.bonuses[0].bonus_id == "bonus-1"


def test_process_order_is_idempotent(clock_now: datetime) -> None:
    orders = InMemoryOrderRepository()
    idempotency = InMemoryIdempotencyRepository()
    pipeline = StubBonusPipeline([sample_bonus("order-1", clock_now)])
    service = AegmallOrderService(
        order_repository=orders,
        idempotency_repository=idempotency,
        bonus_pipeline=pipeline,
        retry_config=RetryConfig(attempts=1),
        clock=lambda: clock_now,
    )

    payload = AegmallOrderPayload(
        order_id="order-1",
        user_id="user-1",
        total_amount=Decimal("200"),
        pv_amount=Decimal("100"),
        channel="ONLINE",
        metadata={"source": "test"},
        idempotency_key="idem-1",
    )

    service.process_order(payload)
    result = service.process_order(payload)

    assert result.status == "duplicate"
    # Pipeline should have been called only once
    assert len(pipeline.calls) == 1


def test_conflicting_payload_raises(clock_now: datetime) -> None:
    orders = InMemoryOrderRepository()
    idempotency = InMemoryIdempotencyRepository()
    pipeline = StubBonusPipeline([])
    service = AegmallOrderService(
        order_repository=orders,
        idempotency_repository=idempotency,
        bonus_pipeline=pipeline,
        retry_config=RetryConfig(attempts=1),
        clock=lambda: clock_now,
    )

    first_payload = AegmallOrderPayload(
        order_id="order-1",
        user_id="user-1",
        total_amount=Decimal("200"),
        pv_amount=Decimal("100"),
        channel="ONLINE",
        metadata={"source": "test"},
        idempotency_key="idem-1",
    )
    service.process_order(first_payload)

    with pytest.raises(IdempotencyConflictError):
        service.process_order(
            AegmallOrderPayload(
                order_id="order-1",
                user_id="user-1",
                total_amount=Decimal("250"),  # different amount triggers conflict
                pv_amount=Decimal("100"),
                channel="ONLINE",
                metadata={"source": "test"},
                idempotency_key="idem-1",
            ),
        )


def test_pipeline_retry_on_transient_failure(clock_now: datetime) -> None:
    orders = InMemoryOrderRepository()
    idempotency = InMemoryIdempotencyRepository()
    pipeline = FlakyBonusPipeline([sample_bonus("order-1", clock_now)], failures=1)
    service = AegmallOrderService(
        order_repository=orders,
        idempotency_repository=idempotency,
        bonus_pipeline=pipeline,
        retry_config=RetryConfig(attempts=2, initial_delay=0),
        clock=lambda: clock_now,
    )

    payload = AegmallOrderPayload(
        order_id="order-1",
        user_id="user-1",
        total_amount=Decimal("200"),
        pv_amount=Decimal("100"),
        channel="ONLINE",
        metadata={"source": "test"},
        idempotency_key="idem-retry",
    )

    result = service.process_order(payload)

    assert result.status == "created"
    assert len(pipeline.calls) == 1  # successful call recorded once
    record = idempotency.get(key="idem-retry", scope="aegmall:user-1")
    assert record is not None and record.status == "SUCCEEDED"


def test_pipeline_failure_marks_idempotency_failed(clock_now: datetime) -> None:
    orders = InMemoryOrderRepository()
    idempotency = InMemoryIdempotencyRepository()
    pipeline = FailingBonusPipeline([])
    service = AegmallOrderService(
        order_repository=orders,
        idempotency_repository=idempotency,
        bonus_pipeline=pipeline,
        retry_config=RetryConfig(attempts=2, initial_delay=0),
        clock=lambda: clock_now,
    )

    payload = AegmallOrderPayload(
        order_id="order-1",
        user_id="user-1",
        total_amount=Decimal("200"),
        pv_amount=Decimal("100"),
        channel="ONLINE",
        metadata={"source": "test"},
        idempotency_key="idem-fail",
    )

    with pytest.raises(RuntimeError):
        service.process_order(payload)

    record = idempotency.get(key="idem-fail", scope="aegmall:user-1")
    assert record is not None and record.status == "FAILED"
