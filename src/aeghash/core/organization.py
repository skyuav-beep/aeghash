"""Organization tree management for unilevel and binary structures."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from aeghash.core.repositories import OrganizationNodeRecord, OrganizationRepository, SpilloverLogRecord


TREE_UNILEVEL = "unilevel"
TREE_BINARY = "binary"


class OrganizationError(ValueError):
    """Base error for organization operations."""


class NodeNotFound(OrganizationError):
    """Raised when a required node is missing."""


class SponsorNotAssigned(OrganizationError):
    """Raised when attempting to add a member without a valid sponsor."""


class OrganizationService:
    """Manage organization nodes with spillover for binary trees."""

    def __init__(
        self,
        repository: OrganizationRepository,
        *,
        id_factory: callable | None = None,
        clock: callable | None = None,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory or (lambda: datetime.now(UTC).strftime("%Y%m%d%H%M%S%f"))
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_root(self, *, tree_type: str, user_id: str) -> OrganizationNodeRecord:
        node_id = self._new_id()
        now = self._now()
        record = OrganizationNodeRecord(
            node_id=node_id,
            user_id=user_id,
            tree_type=tree_type,
            parent_node_id=None,
            sponsor_user_id=None,
            position=None,
            depth=0,
            path=f"/{node_id}",
            created_at=now,
            updated_at=now,
        )
        return self._repository.create_node(record)

    def add_member(
        self,
        *,
        tree_type: str,
        user_id: str,
        sponsor_user_id: str,
    ) -> OrganizationNodeRecord:
        sponsor_node = self._repository.get_node_by_user(tree_type, sponsor_user_id)
        if sponsor_node is None:
            raise SponsorNotAssigned(f"Sponsor '{sponsor_user_id}' not found for {tree_type} tree.")

        if tree_type == TREE_UNILEVEL:
            parent_node = sponsor_node
            position = None
        elif tree_type == TREE_BINARY:
            parent_node, position = self._locate_binary_slot(sponsor_node)
        else:
            raise OrganizationError(f"Unknown tree type: {tree_type}")

        node_id = self._new_id()
        now = self._now()
        record = OrganizationNodeRecord(
            node_id=node_id,
            user_id=user_id,
            tree_type=tree_type,
            parent_node_id=parent_node.node_id,
            sponsor_user_id=sponsor_user_id,
            position=position,
            depth=parent_node.depth + 1,
            path=f"{parent_node.path}/{node_id}",
            created_at=now,
            updated_at=now,
        )
        persisted = self._repository.create_node(record)

        if tree_type == TREE_BINARY and parent_node.node_id != sponsor_node.node_id:
            log = SpilloverLogRecord(
                log_id=self._new_id(),
                tree_type=tree_type,
                sponsor_user_id=sponsor_user_id,
                assigned_user_id=user_id,
                parent_node_id=parent_node.node_id,
                position=position or "",
                created_at=now,
            )
            self._repository.log_spillover(log)
        return persisted

    def get_node(self, node_id: str) -> OrganizationNodeRecord:
        node = self._repository.get_node(node_id)
        if not node:
            raise NodeNotFound(f"Node '{node_id}' not found.")
        return node

    def _locate_binary_slot(self, sponsor_node: OrganizationNodeRecord) -> tuple[OrganizationNodeRecord, str]:
        queue = deque([sponsor_node])
        while queue:
            candidate = queue.popleft()
            children = {child.position: child for child in self._repository.list_children(candidate.node_id)}
            if "L" not in children:
                return candidate, "L"
            if "R" not in children:
                return candidate, "R"
            queue.append(children["L"])
            queue.append(children["R"])
        raise OrganizationError("Unable to find spillover slot in binary tree.")

    def _new_id(self) -> str:
        return str(self._id_factory())

    def _now(self) -> datetime:
        return self._clock()
