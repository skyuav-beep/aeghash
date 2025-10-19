from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Sequence

import pytest
from fastapi import HTTPException

from aeghash.api.kpi import OrganizationKpiAPI, serialize_summary
from aeghash.core.organization_kpi import DailyKpiSnapshot, KpiSummary
from aeghash.core.repositories import (
    OrganizationKpiRecord,
    OrganizationMetricsRepository,
    OrganizationNodeRecord,
    SessionRecord,
)
from aeghash.security.access import AccessContext
from aeghash.utils import NotificationMessage


class StubSessionManager:
    @contextmanager
    def session_scope(self):
        yield object()


class StubSettings:
    def __init__(self, kpi_alerts=None) -> None:
        self.kpi_alerts = kpi_alerts


class StubContainer:
    def __init__(self, *, kpi_alerts=None, notifier=None) -> None:
        self.session_manager = StubSessionManager()
        self.settings = StubSettings(kpi_alerts)
        self.notifier = notifier


class StubNotifier:
    def __init__(self) -> None:
        self.messages: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> None:
        self.messages.append(message)


class StubMetricsRepo(OrganizationMetricsRepository):
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


class StubOrganizationRepo:
    def __init__(self, nodes: Sequence[OrganizationNodeRecord], relations: set[tuple[str, str, str]]) -> None:
        self._nodes = {node.node_id: node for node in nodes}
        self._relations = relations

    def get_node(self, node_id: str) -> OrganizationNodeRecord | None:
        return self._nodes.get(node_id)

    def get_node_by_user(self, tree_type: str, user_id: str) -> OrganizationNodeRecord | None:
        for node in self._nodes.values():
            if node.tree_type == tree_type and node.user_id == user_id:
                return node
        return None

    def is_descendant(self, *, ancestor_node_id: str, descendant_node_id: str, tree_type: str) -> bool:
        return (ancestor_node_id, descendant_node_id, tree_type) in self._relations


def make_record(
    metric_date: date,
    personal: str,
    group: str,
    orders: int,
    *,
    node_id: str = "node-1",
    tree_type: str = "binary",
) -> OrganizationKpiRecord:
    return OrganizationKpiRecord(
        node_id=node_id,
        tree_type=tree_type,
        metric_date=metric_date,
        personal_volume=Decimal(personal),
        group_volume=Decimal(group),
        volume_left=None,
        volume_right=None,
        orders_count=orders,
    )


def make_node(node_id: str, *, user_id: str, tree_type: str = "binary") -> OrganizationNodeRecord:
    timestamp = datetime(2025, 1, 1)
    return OrganizationNodeRecord(
        node_id=node_id,
        user_id=user_id,
        tree_type=tree_type,
        parent_node_id=None,
        sponsor_user_id=None,
        position=None,
        depth=0,
        path=node_id,
        created_at=timestamp,
        updated_at=timestamp,
        rank=None,
        center_id=None,
    )


def test_organization_kpi_api_returns_summary() -> None:
    today = date.today()
    records = [
        make_record(today - timedelta(days=1), "5", "15", 2),
        make_record(today, "10", "20", 3),
    ]
    repo = StubMetricsRepo(records)
    api = OrganizationKpiAPI(StubContainer(), repository_factory=lambda _session: repo)

    summary = api.get_summary("node-1", "binary", days=2)

    assert summary.total_personal_volume == Decimal("15")
    assert summary.total_orders == 5
    assert len(summary.daily) == 2


def test_serialize_summary_formats_decimals() -> None:
    today = date(2025, 1, 5)
    summary = KpiSummary(
        node_id="node",
        tree_type="binary",
        period_start=today - timedelta(days=1),
        period_end=today,
        total_personal_volume=Decimal("12.3456"),
        total_group_volume=Decimal("34.5678"),
        total_orders=4,
        latest_personal_volume=Decimal("6.789"),
        latest_group_volume=Decimal("12.345"),
        latest_volume_left=Decimal("1.23"),
        latest_volume_right=None,
        daily=[
            DailyKpiSnapshot(
                metric_date=today,
                personal_volume=Decimal("6.789"),
                group_volume=Decimal("12.345"),
                orders_count=2,
                volume_left=Decimal("1.23"),
                volume_right=None,
            ),
        ],
    )

    payload = serialize_summary(summary)

    assert payload["totals"]["personal_volume"] == "12.3456"
    assert payload["latest"]["volume_right"] is None
    assert payload["daily"][0]["orders_count"] == 2


def test_kpi_api_enforces_rls_for_user_scope() -> None:
    today = date.today()
    records = [
        make_record(today, "5", "10", 1, node_id="node-2"),
    ]
    metrics_repo = StubMetricsRepo(records)
    org_repo = StubOrganizationRepo(
        [
            make_node("node-1", user_id="user-1"),
            make_node("node-2", user_id="user-2"),
        ],
        relations={("node-1", "node-2", "binary")},
    )
    container = StubContainer()
    api = OrganizationKpiAPI(
        container,
        repository_factory=lambda _session: metrics_repo,
        organization_repo_factory=lambda _session: org_repo,
    )
    access = AccessContext.from_session(
        SessionRecord(
            token="tok",
            user_id="user-1",
            roles=("support",),
            expires_at=0.0,
        ),
    )

    summary = api.get_summary("node-2", "binary", access=access)

    assert summary.node_id == "node-2"


def test_kpi_api_denies_access_outside_scope() -> None:
    today = date.today()
    records = [
        make_record(today, "5", "10", 1, node_id="node-2"),
    ]
    metrics_repo = StubMetricsRepo(records)
    org_repo = StubOrganizationRepo(
        [
            make_node("node-1", user_id="user-1"),
            make_node("node-2", user_id="user-2"),
        ],
        relations=set(),
    )
    container = StubContainer()
    api = OrganizationKpiAPI(
        container,
        repository_factory=lambda _session: metrics_repo,
        organization_repo_factory=lambda _session: org_repo,
    )
    access = AccessContext.from_session(
        SessionRecord(
            token="tok",
            user_id="user-3",
            roles=("support",),
            expires_at=0.0,
        ),
    )

    with pytest.raises(HTTPException) as exc:
        api.get_summary("node-2", "binary", access=access)

    assert exc.value.status_code == 403


def test_kpi_api_allows_scoped_node_access() -> None:
    today = date.today()
    records = [
        make_record(today, "5", "10", 1, node_id="node-3"),
    ]
    metrics_repo = StubMetricsRepo(records)
    org_repo = StubOrganizationRepo(
        [
            make_node("node-3", user_id="user-9"),
        ],
        relations=set(),
    )
    container = StubContainer()
    api = OrganizationKpiAPI(
        container,
        repository_factory=lambda _session: metrics_repo,
        organization_repo_factory=lambda _session: org_repo,
    )
    access = AccessContext.from_session(
        SessionRecord(
            token="tok",
            user_id="user-1",
            roles=("support", "scope:kpi:node:binary:node-3"),
            expires_at=0.0,
        ),
    )

    summary = api.get_summary("node-3", "binary", access=access)

    assert summary.node_id == "node-3"


def test_kpi_api_emits_monitoring_alerts_when_below_threshold() -> None:
    today = date.today()
    records = [
        make_record(today, "1", "2", 0, node_id="node-4"),
    ]
    metrics_repo = StubMetricsRepo(records)
    org_repo = StubOrganizationRepo(
        [
            make_node("node-4", user_id="user-4"),
        ],
        relations=set(),
    )
    notifier = StubNotifier()
    alerts = type(
        "Alerts",
        (),
        {
            "personal_volume_floor": Decimal("5"),
            "group_volume_floor": Decimal("3"),
        },
    )()
    container = StubContainer(kpi_alerts=alerts, notifier=notifier)
    api = OrganizationKpiAPI(
        container,
        repository_factory=lambda _session: metrics_repo,
        organization_repo_factory=lambda _session: org_repo,
    )
    access = AccessContext.from_session(
        SessionRecord(
            token="tok",
            user_id="user-4",
            roles=("support",),
            expires_at=0.0,
        ),
    )

    api.get_summary("node-4", "binary", access=access)

    assert notifier.messages
    assert "personal_volume" in notifier.messages[0].body
