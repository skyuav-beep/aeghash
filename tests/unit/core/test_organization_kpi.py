from datetime import date
from decimal import Decimal
from typing import Sequence

from aeghash.core.organization_kpi import OrganizationKpiService
from aeghash.core.repositories import OrganizationKpiRecord, OrganizationMetricsRepository


class StubMetricsRepository(OrganizationMetricsRepository):
    def __init__(self, records: Sequence[OrganizationKpiRecord]) -> None:
        self._records = list(records)

    def list_metrics(
        self,
        node_id: str,
        *,
        tree_type: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[OrganizationKpiRecord]:
        return [
            record
            for record in self._records
            if record.node_id == node_id
            and record.tree_type == tree_type
            and start_date <= record.metric_date <= end_date
        ]


def make_record(metric_date: date, *, personal: str, group: str, orders: int, left: str | None = None, right: str | None = None) -> OrganizationKpiRecord:
    return OrganizationKpiRecord(
        node_id="node-1",
        tree_type="binary",
        metric_date=metric_date,
        personal_volume=Decimal(personal),
        group_volume=Decimal(group),
        volume_left=Decimal(left) if left is not None else None,
        volume_right=Decimal(right) if right is not None else None,
        orders_count=orders,
    )


def test_kpi_summary_fills_missing_days() -> None:
    records = [
        make_record(date(2025, 1, 1), personal="10", group="30", orders=3, left="5", right="7"),
        make_record(date(2025, 1, 3), personal="20", group="40", orders=2, left="6", right="8"),
    ]
    repo = StubMetricsRepository(records)
    service = OrganizationKpiService(repo, today_factory=lambda: date(2025, 1, 3))

    summary = service.get_summary("node-1", "binary", days=3)

    assert summary.period_start == date(2025, 1, 1)
    assert summary.period_end == date(2025, 1, 3)
    assert summary.total_personal_volume == Decimal("30")
    assert summary.total_group_volume == Decimal("70")
    assert summary.total_orders == 5
    assert len(summary.daily) == 3
    assert summary.daily[1].personal_volume == Decimal("0")
    assert summary.latest_personal_volume == Decimal("20")
    assert summary.latest_volume_left == Decimal("6")


def test_kpi_summary_without_records_returns_zeros() -> None:
    repo = StubMetricsRepository([])
    service = OrganizationKpiService(repo, today_factory=lambda: date(2025, 1, 10))

    summary = service.get_summary("node-1", "binary", days=1)

    assert summary.total_personal_volume == Decimal("0")
    assert summary.total_orders == 0
    assert summary.latest_volume_left is None
