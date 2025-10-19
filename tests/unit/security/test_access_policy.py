from aeghash.core.repositories import SessionRecord
from aeghash.security.access import AccessContext, AccessPolicy


def test_access_context_parses_scopes_and_roles() -> None:
    session = SessionRecord(
        token="token",
        user_id="operator-1",
        roles=("support", "scope:kpi:node:binary:node-123", "scope:other:raw"),
        expires_at=0.0,
    )

    context = AccessContext.from_session(session)

    assert context.roles == ("support",)
    assert "kpi:read" in context.permissions
    assert context.scopes["kpi"] == {"node:binary:node-123"}


def test_access_policy_allowed_kpi_nodes_maps_tree_scope() -> None:
    session = SessionRecord(
        token="token",
        user_id="operator-1",
        roles=(
            "support",
            "scope:kpi:node:binary:node-123",
            "scope:kpi:node:node-999",
        ),
        expires_at=0.0,
    )
    policy = AccessPolicy(AccessContext.from_session(session))

    scoped = policy.allowed_kpi_nodes()

    assert scoped["binary"] == {"node-123"}
    assert scoped[None] == {"node-999"}


def test_access_policy_personal_data_flag() -> None:
    session = SessionRecord(
        token="token",
        user_id="fin-1",
        roles=("finance",),
        expires_at=0.0,
    )
    policy = AccessPolicy(AccessContext.from_session(session))

    assert policy.can_view_full_personal_data()
