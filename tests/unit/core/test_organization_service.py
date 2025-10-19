from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aeghash.core.organization import TREE_BINARY, TREE_UNILEVEL, OrganizationService
from aeghash.utils.memory_repositories import InMemoryOrganizationRepository


@pytest.fixture()
def repository() -> InMemoryOrganizationRepository:
    return InMemoryOrganizationRepository()


@pytest.fixture()
def service(repository: InMemoryOrganizationRepository) -> OrganizationService:
    counter = {"value": 0}

    def id_factory() -> str:
        counter["value"] += 1
        return f"node-{counter['value']}"

    return OrganizationService(repository, id_factory=id_factory, clock=lambda: datetime(2025, 1, 1, tzinfo=UTC))


def test_create_root_and_add_unilevel_member(service: OrganizationService, repository: InMemoryOrganizationRepository):
    root = service.create_root(tree_type=TREE_UNILEVEL, user_id="root-user")
    member = service.add_member(tree_type=TREE_UNILEVEL, user_id="child", sponsor_user_id="root-user")

    assert member.parent_node_id == root.node_id
    assert member.depth == 1
    assert repository.list_children(root.node_id)[0].user_id == "child"


def test_add_binary_members_with_spillover(service: OrganizationService, repository: InMemoryOrganizationRepository):
    root = service.create_root(tree_type=TREE_BINARY, user_id="root")
    service.add_member(tree_type=TREE_BINARY, user_id="left", sponsor_user_id="root")
    service.add_member(tree_type=TREE_BINARY, user_id="right", sponsor_user_id="root")
    third = service.add_member(tree_type=TREE_BINARY, user_id="spillover", sponsor_user_id="root")

    assert third.parent_node_id != root.node_id  # spilled over below root
    spillovers = repository.list_spillovers("root")
    assert spillovers[-1].assigned_user_id == "spillover"


def test_binary_spillover_depth_order(service: OrganizationService, repository: InMemoryOrganizationRepository):
    service.create_root(tree_type=TREE_BINARY, user_id="sponsor")
    names = ["a", "b", "c", "d", "e", "f", "g"]
    for name in names:
        service.add_member(tree_type=TREE_BINARY, user_id=name, sponsor_user_id="sponsor")

    # ensure depth increases as expected
    nodes = [repository.get_node_by_user(TREE_BINARY, user_id) for user_id in names]
    depths = [node.depth for node in nodes if node is not None]
    assert max(depths) >= 2
