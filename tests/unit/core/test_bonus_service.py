from __future__ import annotations

from decimal import Decimal
from datetime import UTC, datetime

import pytest

from aeghash.core.bonus import BonusContext, BonusRule, BonusService
from aeghash.core.organization import OrganizationService, TREE_UNILEVEL
from aeghash.utils import InMemoryBonusRepository, InMemoryOrganizationRepository


@pytest.fixture()
def organization_repo() -> InMemoryOrganizationRepository:
    return InMemoryOrganizationRepository()


@pytest.fixture()
def bonus_repo() -> InMemoryBonusRepository:
    return InMemoryBonusRepository()


@pytest.fixture()
def organization_service(organization_repo: InMemoryOrganizationRepository) -> OrganizationService:
    counter = {"value": 0}

    def id_factory() -> str:
        counter["value"] += 1
        return f"node-{counter['value']}"

    return OrganizationService(organization_repo, id_factory=id_factory, clock=lambda: datetime(2025, 1, 1, tzinfo=UTC))


@pytest.fixture()
def bonus_service(organization_repo: InMemoryOrganizationRepository, bonus_repo: InMemoryBonusRepository) -> BonusService:
    rules = [
        BonusRule(
            bonus_type="recommend",
            tree_type=TREE_UNILEVEL,
            percentages=[Decimal("0.3"), Decimal("0.1"), Decimal("0.05")],
        ),
    ]
    counter = {"value": 0}

    def id_factory() -> str:
        counter["value"] += 1
        return f"bonus-{counter['value']}"

    return BonusService(
        organization_repo,
        bonus_repo,
        rules,
        id_factory=id_factory,
        clock=lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
    )


def build_tree(service: OrganizationService) -> None:
    service.create_root(tree_type=TREE_UNILEVEL, user_id="root")
    service.add_member(tree_type=TREE_UNILEVEL, user_id="sponsor", sponsor_user_id="root")
    service.add_member(tree_type=TREE_UNILEVEL, user_id="member", sponsor_user_id="sponsor")


def test_bonus_distribution_creates_entries(
    organization_service: OrganizationService,
    bonus_service: BonusService,
    bonus_repo: InMemoryBonusRepository,
) -> None:
    build_tree(organization_service)

    context = BonusContext(
        order_id="order-1",
        user_id="member",
        amount=Decimal("100"),
        metadata={},
    )

    entries = bonus_service.distribute(context)

    assert len(entries) == 2  # sponsor + root
    first_entry = entries[0]
    assert first_entry.user_id == "sponsor"
    assert first_entry.bonus_amount == Decimal("30")
    second_entry = entries[1]
    assert second_entry.user_id == "root"
    assert second_entry.bonus_amount == Decimal("10")
    stored = sorted(bonus_repo.records.values(), key=lambda entry: entry.level)
    expected = sorted(entries, key=lambda entry: entry.level)
    assert stored == expected
