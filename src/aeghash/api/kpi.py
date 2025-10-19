"""API layer for organization KPI dashboards."""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Mapping, Set

from fastapi import HTTPException
from sqlalchemy.orm import Session

from aeghash.core.organization_kpi import KpiSummary, OrganizationKpiService
from aeghash.core.repositories import OrganizationMetricsRepository, OrganizationRepository
from aeghash.infrastructure.bootstrap import ServiceContainer
from aeghash.infrastructure.repositories import (
    SqlAlchemyOrganizationMetricsRepository,
    SqlAlchemyOrganizationRepository,
)
from aeghash.security.access import AccessContext, AccessPolicy
from aeghash.utils import NotificationMessage


def _decimal_to_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def serialize_summary(summary: KpiSummary) -> dict[str, object]:
    return {
        "node_id": summary.node_id,
        "tree_type": summary.tree_type,
        "period": {
            "start": summary.period_start.isoformat(),
            "end": summary.period_end.isoformat(),
        },
        "totals": {
            "personal_volume": _decimal_to_str(summary.total_personal_volume),
            "group_volume": _decimal_to_str(summary.total_group_volume),
            "orders": summary.total_orders,
        },
        "latest": {
            "personal_volume": _decimal_to_str(summary.latest_personal_volume),
            "group_volume": _decimal_to_str(summary.latest_group_volume),
            "volume_left": _decimal_to_str(summary.latest_volume_left),
            "volume_right": _decimal_to_str(summary.latest_volume_right),
        },
        "daily": [
            {
                "date": snapshot.metric_date.isoformat(),
                "personal_volume": _decimal_to_str(snapshot.personal_volume),
                "group_volume": _decimal_to_str(snapshot.group_volume),
                "orders_count": snapshot.orders_count,
                "volume_left": _decimal_to_str(snapshot.volume_left),
                "volume_right": _decimal_to_str(snapshot.volume_right),
            }
            for snapshot in summary.daily
        ],
    }


class OrganizationKpiAPI:
    """Facade for retrieving organization KPI summaries."""

    def __init__(
        self,
        container: ServiceContainer,
        *,
        repository_factory: Callable[[Session], OrganizationMetricsRepository] | None = None,
        organization_repo_factory: Callable[[Session], OrganizationRepository] | None = None,
    ) -> None:
        self._container = container
        self._repository_factory = repository_factory or SqlAlchemyOrganizationMetricsRepository
        self._organization_repo_factory = organization_repo_factory or SqlAlchemyOrganizationRepository

    @classmethod
    def from_container(
        cls,
        container: ServiceContainer,
        *,
        repository_factory: Callable[[Session], OrganizationMetricsRepository] | None = None,
        organization_repo_factory: Callable[[Session], OrganizationRepository] | None = None,
    ) -> "OrganizationKpiAPI":
        return cls(
            container,
            repository_factory=repository_factory,
            organization_repo_factory=organization_repo_factory,
        )

    def get_summary(
        self,
        node_id: str,
        tree_type: str,
        *,
        days: int = 7,
        access: AccessContext | None = None,
    ) -> KpiSummary:
        if days <= 0 or days > 90:
            raise HTTPException(status_code=400, detail="invalid_days")

        with self._container.session_manager.session_scope() as session:
            repository = self._repository_factory(session)
            organization_repo = None
            if access is not None:
                organization_repo = self._organization_repo_factory(session)
                self._enforce_access(organization_repo, access, node_id=node_id, tree_type=tree_type)

            service = OrganizationKpiService(repository)
            summary = service.get_summary(node_id=node_id, tree_type=tree_type, days=days)
            self._dispatch_alerts(summary)
            return summary

    # ------------------------------------------------------------------ internal helpers

    def _enforce_access(
        self,
        organization_repo: OrganizationRepository,
        access: AccessContext,
        *,
        node_id: str,
        tree_type: str,
    ) -> None:
        policy = AccessPolicy(access)
        if policy.has_global_kpi_access():
            return

        node = organization_repo.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="organization_node_not_found")
        if node.tree_type != tree_type:
            raise HTTPException(status_code=400, detail="invalid_tree_type")

        scoped_nodes = policy.allowed_kpi_nodes()
        if scoped_nodes:
            if self._is_node_in_scope(organization_repo, node_id, tree_type, scoped_nodes):
                return
            raise HTTPException(status_code=403, detail="forbidden")

        owner_node = organization_repo.get_node_by_user(tree_type, access.user_id)
        if owner_node is None:
            raise HTTPException(status_code=403, detail="forbidden")
        if owner_node.node_id == node_id:
            return
        if organization_repo.is_descendant(
            ancestor_node_id=owner_node.node_id,
            descendant_node_id=node_id,
            tree_type=tree_type,
        ):
            return
        raise HTTPException(status_code=403, detail="forbidden")

    def _is_node_in_scope(
        self,
        organization_repo: OrganizationRepository,
        node_id: str,
        tree_type: str,
        scoped_nodes: Mapping[str | None, Set[str]],
    ) -> bool:
        direct_matches = scoped_nodes.get(None, set())
        if node_id in direct_matches:
            return True

        scoped_for_tree = scoped_nodes.get(tree_type, set())
        if node_id in scoped_for_tree:
            return True

        all_candidates = direct_matches | scoped_for_tree
        for candidate in all_candidates:
            if organization_repo.is_descendant(
                ancestor_node_id=candidate,
                descendant_node_id=node_id,
                tree_type=tree_type,
            ):
                return True
        return False

    def _dispatch_alerts(self, summary: KpiSummary) -> None:
        notifier = self._container.notifier
        alert_settings = getattr(self._container.settings, "kpi_alerts", None)
        if not notifier or not alert_settings:
            return

        breaches: list[str] = []
        if (
            getattr(alert_settings, "personal_volume_floor", None) is not None
            and summary.latest_personal_volume < alert_settings.personal_volume_floor
        ):
            breaches.append(
                "personal_volume"
                + " below floor ("
                + f"{_decimal_to_str(summary.latest_personal_volume)}"
                + " < "
                + f"{_decimal_to_str(alert_settings.personal_volume_floor)}"
                + ")"
            )
        if (
            getattr(alert_settings, "group_volume_floor", None) is not None
            and summary.latest_group_volume < alert_settings.group_volume_floor
        ):
            breaches.append(
                "group_volume"
                + " below floor ("
                + f"{_decimal_to_str(summary.latest_group_volume)}"
                + " < "
                + f"{_decimal_to_str(alert_settings.group_volume_floor)}"
                + ")"
            )

        if not breaches:
            return

        body_lines = [
            f"KPI alert for node {summary.node_id} ({summary.tree_type})",
            *breaches,
        ]
        notifier.send(
            NotificationMessage(
                subject="KPI Alert",
                body="\n".join(body_lines),
            ),
        )
