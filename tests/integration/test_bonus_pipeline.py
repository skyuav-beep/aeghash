from datetime import UTC, datetime
from decimal import Decimal

from aeghash.core.bonus_pipeline import BonusPipeline, OrderEvent
from aeghash.core.organization import OrganizationService, TREE_BINARY, TREE_UNILEVEL
from aeghash.infrastructure import (
    Base,
    SqlAlchemyBonusRepository,
    SqlAlchemyOrganizationRepository,
    create_engine_and_session,
)
from aeghash.infrastructure.repositories import BonusEntryModel


def build_trees(service: OrganizationService) -> None:
    service.create_root(tree_type=TREE_UNILEVEL, user_id="root")
    service.add_member(tree_type=TREE_UNILEVEL, user_id="sponsor", sponsor_user_id="root")
    service.add_member(tree_type=TREE_UNILEVEL, user_id="member", sponsor_user_id="sponsor")

    service.create_root(tree_type=TREE_BINARY, user_id="root")
    service.add_member(tree_type=TREE_BINARY, user_id="sponsor", sponsor_user_id="root")
    service.add_member(tree_type=TREE_BINARY, user_id="member", sponsor_user_id="sponsor")


def test_bonus_pipeline_with_sqlalchemy_repositories():
    engine, SessionLocal = create_engine_and_session("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        clock = lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
        org_repo = SqlAlchemyOrganizationRepository(session)
        bonus_repo = SqlAlchemyBonusRepository(session)

        node_counter = {"value": 0}

        def node_id_factory() -> str:
            node_counter["value"] += 1
            return f"node-{node_counter['value']}"

        org_service = OrganizationService(org_repo, id_factory=node_id_factory, clock=clock)
        build_trees(org_service)
        session.commit()

        bonus_counter = {"value": 0}

        def bonus_id_factory() -> str:
            bonus_counter["value"] += 1
            return f"bonus-{bonus_counter['value']}"

        pipeline = BonusPipeline(
            org_repo,
            bonus_repo,
            id_factory=bonus_id_factory,
            clock=clock,
        )

        event = OrderEvent(
            order_id="order-1",
            user_id="member",
            pv_amount=Decimal("100"),
            total_amount=Decimal("200"),
            metadata={},
        )
        pipeline.process_order(event)
        session.commit()

        entries = session.query(BonusEntryModel).all()
        assert entries
        types = {entry.bonus_type for entry in entries}
        assert "recommend" in types
        assert "sponsor" in types
    finally:
        session.close()
        engine.dispose()
