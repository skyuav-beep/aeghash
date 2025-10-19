from datetime import UTC, datetime
from decimal import Decimal

from aeghash.core.bonus_closing import BonusClosingService
from aeghash.core.repositories import BonusEntryRecord
from aeghash.utils import InMemoryBonusRepository


def test_bonus_closing_confirms_and_schedules_retry():
    repo = InMemoryBonusRepository()
    created = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    success_entry = BonusEntryRecord(
        bonus_id="bonus-success",
        user_id="user-1",
        source_user_id="order-user",
        bonus_type="recommend",
        order_id="order-1",
        level=1,
        pv_amount=Decimal("100"),
        bonus_amount=Decimal("10"),
        status="PENDING",
        metadata={},
        created_at=created,
    )
    failing_entry = BonusEntryRecord(
        bonus_id="bonus-fail",
        user_id="user-2",
        source_user_id="order-user",
        bonus_type="recommend",
        order_id="order-1",
        level=2,
        pv_amount=Decimal("100"),
        bonus_amount=Decimal("5"),
        status="PENDING",
        metadata={},
        created_at=created,
    )
    repo.record_bonus(success_entry)
    repo.record_bonus(failing_entry)

    credited = []

    def wallet_creditor(payload):
        if payload["user_id"] == "user-2":
            raise RuntimeError("wallet blocked")
        credited.append(payload)

    service = BonusClosingService(
        repo,
        wallet_creditor=wallet_creditor,
        now_factory=lambda: datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
        id_factory=lambda: "closing-job",
        retry_backoff_minutes=15,
        max_retries=3,
    )

    job = service.run_closing()

    assert job.total_entries == 2
    assert job.confirmed_entries == 1
    assert job.retry_entries == 1
    assert credited[0]["user_id"] == "user-1"
    retry_entry = repo.records["bonus-fail"]
    assert retry_entry.status == "RETRY"
    assert retry_entry.metadata["retry_after"].startswith("2025-01-01T13:15")
