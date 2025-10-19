"""Bonus distribution engine based on organization hierarchies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable, Mapping, Sequence

from aeghash.core.repositories import BonusEntryRecord, BonusRepository, OrganizationRepository


@dataclass(slots=True)
class BonusRule:
    """Configuration for a specific bonus type."""

    bonus_type: str
    percentages: Sequence[Decimal]
    tree_type: str


@dataclass(slots=True)
class BonusContext:
    order_id: str
    user_id: str
    amount: Decimal
    metadata: Mapping[str, object]


class BonusService:
    """Distribute bonuses according to configured percentage rules."""

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        bonus_repository: BonusRepository,
        rules: Sequence[BonusRule],
        *,
        id_factory: callable | None = None,
        clock: callable | None = None,
    ) -> None:
        self._organizations = organization_repository
        self._bonuses = bonus_repository
        self._rules = list(rules)
        self._id_factory = id_factory or (lambda: datetime.now(UTC).strftime("%Y%m%d%H%M%S%f"))
        self._clock = clock or (lambda: datetime.now(UTC))

    def distribute(self, context: BonusContext) -> list[BonusEntryRecord]:
        node = self._organizations.get_node_by_user(self._rules[0].tree_type, context.user_id)
        if node is None:
            raise ValueError(f"User '{context.user_id}' is not registered in organization tree '{self._rules[0].tree_type}'.")

        results: list[BonusEntryRecord] = []
        for rule in self._rules:
            results.extend(self._distribute_for_rule(rule, node, context))
        return results

    # ------------------------------------------------------------------ helpers

    def _distribute_for_rule(
        self,
        rule: BonusRule,
        node,
        context: BonusContext,
    ) -> list[BonusEntryRecord]:
        ancestors = self._collect_ancestors(node, max_levels=len(rule.percentages))
        created: list[BonusEntryRecord] = []
        for level, (ancestor_id, ancestor_node) in enumerate(ancestors, start=1):
            percentage = rule.percentages[level - 1]
            if percentage <= 0:
                continue
            amount = (context.amount * percentage).quantize(Decimal("0.0001"))
            record = BonusEntryRecord(
                bonus_id=self._new_id(),
                user_id=ancestor_node.user_id,
                source_user_id=context.user_id,
                bonus_type=rule.bonus_type,
                order_id=context.order_id,
                level=level,
                pv_amount=context.amount,
                bonus_amount=amount,
                status="PENDING",
                metadata={
                    "order_id": context.order_id,
                    "tree_type": rule.tree_type,
                    "source_node_id": node.node_id,
                    "ancestor_node_id": ancestor_id,
                    "pv_amount": str(context.amount),
                } | dict(context.metadata),
                created_at=self._now(),
            )
            self._bonuses.record_bonus(record)
            created.append(record)
        return created

    def _collect_ancestors(
        self,
        node,
        *,
        max_levels: int,
    ) -> Iterable[tuple[str, object]]:
        path_ids = [segment for segment in node.path.split("/") if segment]
        ancestor_ids = list(reversed(path_ids[:-1]))  # exclude current node
        ancestor_ids = ancestor_ids[:max_levels]
        if not ancestor_ids:
            return []
        nodes = self._organizations.get_nodes_by_ids(ancestor_ids)
        lookup = {record.node_id: record for record in nodes}
        return [(ancestor_id, lookup[ancestor_id]) for ancestor_id in ancestor_ids if ancestor_id in lookup]

    def _new_id(self) -> str:
        return str(self._id_factory())

    def _now(self) -> datetime:
        return self._clock()
