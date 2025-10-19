from datetime import UTC, datetime
from decimal import Decimal

import pytest

from aeghash.core.bonus_retry import BonusRetryService
from aeghash.core.repositories import BonusEntryRecord
from aeghash.utils import InMemoryBonusRepository


@pytest.fixture()
def base_time() -> datetime:
    return datetime(2025, 1, 1, 12, 0, tzinfo=UTC)


def create_bonus_entry(bonus_id: str, *, created_at: datetime) -> BonusEntryRecord:
    return BonusEntryRecord(
        bonus_id=bonus_id,
        user_id="user-1",
        source_user_id="member-1",
        bonus_type="recommend",
        order_id="order-1",
        level=1,
        pv_amount=Decimal("100"),
        bonus_amount=Decimal("10"),
        status="PENDING",
        metadata={},
        created_at=created_at,
    )


def test_bonus_retry_processes_successful_retry(base_time: datetime) -> None:
    repo = InMemoryBonusRepository()
    entry = create_bonus_entry("bonus-1", created_at=base_time)
    repo.record_bonus(entry)
    repo.schedule_retry(
        "bonus-1",
        retry_after=base_time,
        metadata={"retry_count": 1, "last_error": "transient"},
    )

    credited = []

    def wallet_creditor(payload):
        credited.append(payload)

    service = BonusRetryService(
        repo,
        wallet_creditor=wallet_creditor,
        now_factory=lambda: base_time,
        base_delay_minutes=15,
        max_retries=3,
    )

    result = service.process()

    assert result.processed == 1
    assert result.succeeded == 1
    assert repo.records["bonus-1"].status == "CONFIRMED"
    queue = repo.retry_queue["retry-bonus-1"]
    assert queue.status == "COMPLETED"
    assert credited[0]["user_id"] == "user-1"


def test_bonus_retry_reschedules_and_marks_failed(base_time: datetime) -> None:
    repo = InMemoryBonusRepository()
    entry = create_bonus_entry("bonus-2", created_at=base_time)
    repo.record_bonus(entry)
    repo.schedule_retry(
        "bonus-2",
        retry_after=base_time,
        metadata={"retry_count": 1, "last_error": "initial"},
    )

    attempts = {"count": 0}

    def failing_creditor(_payload):
        attempts["count"] += 1
        raise RuntimeError(f"failure-{attempts['count']}")

    service = BonusRetryService(
        repo,
        wallet_creditor=failing_creditor,
        now_factory=lambda: base_time,
        base_delay_minutes=0,
        max_retries=3,
    )

    first_result = service.process()
    assert first_result.rescheduled == 1
    queue = repo.retry_queue["retry-bonus-2"]
    assert queue.status == "PENDING"
    assert queue.retry_count == 2
    assert repo.records["bonus-2"].status == "RETRY"

    second_result = service.process()
    assert second_result.failed == 1
    queue = repo.retry_queue["retry-bonus-2"]
    assert queue.status == "FAILED"
    assert repo.records["bonus-2"].status == "FAILED"
