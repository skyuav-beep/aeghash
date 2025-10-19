"""Order-driven bonus distribution pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
from typing import Mapping, Optional, Sequence

from aeghash.core.bonus import BonusContext, BonusRule, BonusService
from aeghash.core.repositories import BonusEntryRecord, BonusRepository, OrganizationRepository


@dataclass(slots=True)
class OrderEvent:
    """Normalized order event used by the bonus pipeline."""

    order_id: str
    user_id: str
    pv_amount: Decimal
    total_amount: Decimal
    metadata: Mapping[str, object] | None = None


class BonusPipeline:
    """Coordinates bonus distribution for paid order events."""

    SHARE_PERCENT = Decimal("0.05")
    CENTER_PERCENT = Decimal("0.08")
    CENTER_REF_PERCENT = Decimal("0.02")

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        bonus_repository: BonusRepository,
        *,
        id_factory: callable | None = None,
        clock: callable | None = None,
        share_percent: Decimal | None = None,
        center_percent: Decimal | None = None,
        center_ref_percent: Decimal | None = None,
    ) -> None:
        self._organizations = organization_repository
        self._bonuses = bonus_repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_counter = 0
        self._id_factory = id_factory or self._default_id_factory

        self._share_percent = share_percent if share_percent is not None else self.SHARE_PERCENT
        self._center_percent = center_percent if center_percent is not None else self.CENTER_PERCENT
        self._center_ref_percent = (
            center_ref_percent if center_ref_percent is not None else self.CENTER_REF_PERCENT
        )

        self._recommend_service = BonusService(
            organization_repository,
            bonus_repository,
            [
                BonusRule(
                    bonus_type="recommend",
                    tree_type="unilevel",
                    percentages=self._recommend_percentages(),
                ),
            ],
            id_factory=self._next_bonus_id,
            clock=self._clock,
        )
        self._binary_service = BonusService(
            organization_repository,
            bonus_repository,
            [
                BonusRule(
                    bonus_type="sponsor",
                    tree_type="binary",
                    percentages=self._binary_percentages(),
                ),
            ],
            id_factory=self._next_bonus_id,
            clock=self._clock,
        )

    def process_order(self, event: OrderEvent) -> list[BonusEntryRecord]:
        """Execute bonus calculations for a single order."""
        metadata = event.metadata or {}
        context = BonusContext(
            order_id=event.order_id,
            user_id=event.user_id,
            amount=event.pv_amount,
            metadata=metadata,
        )

        records: list[BonusEntryRecord] = []
        records.extend(self._recommend_service.distribute(context))
        records.extend(self._binary_service.distribute(context))

        records.extend(self._apply_share_bonus(event, metadata))
        records.extend(self._apply_center_bonuses(event, metadata))
        return records

    # ---------------------------------------------------------------- Direct bonuses

    def _apply_share_bonus(
        self,
        event: OrderEvent,
        metadata: Mapping[str, object],
    ) -> list[BonusEntryRecord]:
        if self._share_percent <= 0:
            return []
        amount = self._quantize(event.total_amount * self._share_percent)
        if amount <= 0:
            return []
        meta = {"order_id": event.order_id, "pv_amount": str(event.pv_amount), "basis": "share"} | dict(metadata)
        record = self._create_bonus_record(
            user_id=event.user_id,
            source_user_id=event.user_id,
            bonus_type="share",
            level=0,
            bonus_amount=amount,
            order_id=event.order_id,
            pv_amount=event.pv_amount,
            status="PENDING",
            metadata=meta,
        )
        self._bonuses.record_bonus(record)
        return [record]

    def _apply_center_bonuses(
        self,
        event: OrderEvent,
        metadata: Mapping[str, object],
    ) -> list[BonusEntryRecord]:
        records: list[BonusEntryRecord] = []
        center_user_id = metadata.get("center_user_id")
        ref_user_id = metadata.get("center_referrer_user_id")

        if center_user_id and self._center_percent > 0:
            amount = self._quantize(event.total_amount * self._center_percent)
            if amount > 0:
                meta = {
                    "order_id": event.order_id,
                    "pv_amount": str(event.pv_amount),
                    "basis": "center",
                } | dict(metadata)
                record = self._create_bonus_record(
                    user_id=str(center_user_id),
                    source_user_id=event.user_id,
                    bonus_type="center",
                    level=0,
                    bonus_amount=amount,
                    order_id=event.order_id,
                    pv_amount=event.pv_amount,
                    status="PENDING",
                    metadata=meta,
                )
                self._bonuses.record_bonus(record)
                records.append(record)

        if ref_user_id and self._center_ref_percent > 0:
            amount = self._quantize(event.total_amount * self._center_ref_percent)
            if amount > 0:
                meta = {
                    "order_id": event.order_id,
                    "pv_amount": str(event.pv_amount),
                    "basis": "center_referral",
                } | dict(metadata)
                record = self._create_bonus_record(
                    user_id=str(ref_user_id),
                    source_user_id=event.user_id,
                    bonus_type="center_referral",
                    level=0,
                    bonus_amount=amount,
                    order_id=event.order_id,
                    pv_amount=event.pv_amount,
                    status="PENDING",
                    metadata=meta,
                )
                self._bonuses.record_bonus(record)
                records.append(record)
        return records

    # ---------------------------------------------------------------- utilities

    def _recommend_percentages(self) -> Sequence[Decimal]:
        base = [
            Decimal("0.30"),
            Decimal("0.05"),
            Decimal("0.05"),
            Decimal("0.03"),
            Decimal("0.02"),
        ]
        tail = [Decimal("0.01")] * 5
        return base + tail

    def _binary_percentages(self) -> Sequence[Decimal]:
        return [Decimal("0.01")] * 20

    def _create_bonus_record(
        self,
        *,
        user_id: str,
        source_user_id: str,
        bonus_type: str,
        level: int,
        bonus_amount: Decimal,
        order_id: str,
        pv_amount: Decimal,
        status: str,
        metadata: Mapping[str, object],
    ) -> BonusEntryRecord:
        return BonusEntryRecord(
            bonus_id=self._next_bonus_id(),
            user_id=user_id,
            source_user_id=source_user_id,
            bonus_type=bonus_type,
            order_id=order_id,
            level=level,
            pv_amount=pv_amount,
            bonus_amount=bonus_amount,
            status=status,
            metadata=dict(metadata),
            created_at=self._clock(),
        )

    def _quantize(self, amount: Decimal) -> Decimal:
        return amount.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

    def _default_id_factory(self) -> str:
        self._id_counter += 1
        return f"bonus-{self._id_counter}"

    def _next_bonus_id(self) -> str:
        return str(self._id_factory())
