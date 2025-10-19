"""Aggregates organization KPI metrics for dashboard consumption."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable, Sequence

from aeghash.core.repositories import OrganizationKpiRecord, OrganizationMetricsRepository


ZERO = Decimal("0")


@dataclass(slots=True)
class DailyKpiSnapshot:
    """Daily KPI view for an organization node."""

    metric_date: date
    personal_volume: Decimal
    group_volume: Decimal
    orders_count: int
    volume_left: Decimal | None
    volume_right: Decimal | None


@dataclass(slots=True)
class KpiSummary:
    """Aggregated KPI summary for an organization node."""

    node_id: str
    tree_type: str
    period_start: date
    period_end: date
    total_personal_volume: Decimal
    total_group_volume: Decimal
    total_orders: int
    latest_personal_volume: Decimal
    latest_group_volume: Decimal
    latest_volume_left: Decimal | None
    latest_volume_right: Decimal | None
    daily: Sequence[DailyKpiSnapshot]


class OrganizationKpiService:
    """Compute KPI summaries using stored organization metrics."""

    def __init__(
        self,
        repository: OrganizationMetricsRepository,
        *,
        today_factory: Callable[[], date] | None = None,
    ) -> None:
        self._repository = repository
        self._today = today_factory or date.today

    def get_summary(self, node_id: str, tree_type: str, *, days: int = 7) -> KpiSummary:
        if days <= 0:
            raise ValueError("days must be positive")

        period_end = self._today()
        period_start = period_end - timedelta(days=days - 1)
        records = self._repository.list_metrics(
            node_id,
            tree_type=tree_type,
            start_date=period_start,
            end_date=period_end,
        )
        daily = self._normalize(records, period_start, period_end)

        total_personal = sum((item.personal_volume for item in daily), ZERO)
        total_group = sum((item.group_volume for item in daily), ZERO)
        total_orders = sum(item.orders_count for item in daily)

        latest = daily[-1] if daily else DailyKpiSnapshot(
            metric_date=period_end,
            personal_volume=ZERO,
            group_volume=ZERO,
            orders_count=0,
            volume_left=None,
            volume_right=None,
        )

        return KpiSummary(
            node_id=node_id,
            tree_type=tree_type,
            period_start=period_start,
            period_end=period_end,
            total_personal_volume=total_personal,
            total_group_volume=total_group,
            total_orders=total_orders,
            latest_personal_volume=latest.personal_volume,
            latest_group_volume=latest.group_volume,
            latest_volume_left=latest.volume_left,
            latest_volume_right=latest.volume_right,
            daily=daily,
        )

    # ------------------------------------------------------------------ helpers

    def _normalize(
        self,
        records: Sequence[OrganizationKpiRecord],
        period_start: date,
        period_end: date,
    ) -> list[DailyKpiSnapshot]:
        index = {record.metric_date: record for record in records}
        snapshots: list[DailyKpiSnapshot] = []
        current = period_start
        while current <= period_end:
            record = index.get(current)
            if record is None:
                snapshots.append(
                    DailyKpiSnapshot(
                        metric_date=current,
                        personal_volume=ZERO,
                        group_volume=ZERO,
                        orders_count=0,
                        volume_left=None,
                        volume_right=None,
                    ),
                )
            else:
                snapshots.append(
                    DailyKpiSnapshot(
                        metric_date=record.metric_date,
                        personal_volume=record.personal_volume,
                        group_volume=record.group_volume,
                        orders_count=record.orders_count,
                        volume_left=record.volume_left,
                        volume_right=record.volume_right,
                    ),
                )
            current += timedelta(days=1)
        return snapshots
