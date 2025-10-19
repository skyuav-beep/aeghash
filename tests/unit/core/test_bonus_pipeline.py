from datetime import UTC, datetime
from decimal import Decimal

from aeghash.core.bonus_pipeline import BonusPipeline, OrderEvent
from aeghash.core.organization import OrganizationService, TREE_BINARY, TREE_UNILEVEL
from aeghash.utils import InMemoryBonusRepository, InMemoryOrganizationRepository


def build_trees(service: OrganizationService) -> None:
    # Unilevel tree: root -> sponsor -> member
    service.create_root(tree_type=TREE_UNILEVEL, user_id="root")
    service.add_member(tree_type=TREE_UNILEVEL, user_id="sponsor", sponsor_user_id="root")
    service.add_member(tree_type=TREE_UNILEVEL, user_id="member", sponsor_user_id="sponsor")

    # Binary tree mirrors unilevel for sponsor relationships
    service.create_root(tree_type=TREE_BINARY, user_id="root")
    service.add_member(tree_type=TREE_BINARY, user_id="sponsor", sponsor_user_id="root")
    service.add_member(tree_type=TREE_BINARY, user_id="member", sponsor_user_id="sponsor")


def test_bonus_pipeline_distributes_and_logs_all_bonuses():
    org_repo = InMemoryOrganizationRepository()
    bonus_repo = InMemoryBonusRepository()

    bonus_counter = {"value": 0}

    def bonus_id_factory() -> str:
        bonus_counter["value"] += 1
        return f"bonus-{bonus_counter['value']}"

    node_counter = {"value": 0}

    def node_id_factory() -> str:
        node_counter["value"] += 1
        return f"node-{node_counter['value']}"

    clock = lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    org_service = OrganizationService(org_repo, id_factory=node_id_factory, clock=clock)
    build_trees(org_service)

    pipeline = BonusPipeline(
        org_repo,
        bonus_repo,
        id_factory=bonus_id_factory,
        clock=clock,
        share_percent=Decimal("0.05"),
        center_percent=Decimal("0.08"),
        center_ref_percent=Decimal("0.02"),
    )

    event = OrderEvent(
        order_id="order-1",
        user_id="member",
        pv_amount=Decimal("100"),
        total_amount=Decimal("200"),
        metadata={"center_user_id": "center", "center_referrer_user_id": "referrer"},
    )

    records = pipeline.process_order(event)

    bonus_types = {record.bonus_type for record in records}
    assert bonus_types == {"recommend", "sponsor", "share", "center", "center_referral"}
    assert sum(record.bonus_amount for record in records if record.bonus_type == "recommend") == Decimal("35")
    assert sum(record.bonus_amount for record in records if record.bonus_type == "sponsor") == Decimal("2")
    share_record = next(record for record in records if record.bonus_type == "share")
    assert share_record.bonus_amount == Decimal("10")
    center_record = next(record for record in records if record.bonus_type == "center")
    assert center_record.user_id == "center"
    ref_record = next(record for record in records if record.bonus_type == "center_referral")
    assert ref_record.user_id == "referrer"
    stored = sorted(bonus_repo.records.values(), key=lambda entry: (entry.bonus_type, entry.level))
    expected = sorted(records, key=lambda entry: (entry.bonus_type, entry.level))
    assert stored == expected
