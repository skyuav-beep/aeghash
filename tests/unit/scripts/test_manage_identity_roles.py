import importlib.util
from pathlib import Path

import pytest

from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import SqlAlchemyUserRepository
from aeghash.infrastructure.session import SessionManager

_MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "manage_identity_roles.py"
_SPEC = importlib.util.spec_from_file_location("manage_identity_roles_module", _MODULE_PATH)
assert _SPEC and _SPEC.loader  # pragma: no cover - defensive
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)  # type: ignore[arg-type]

MANAGE_ROLES = _MODULE
update_identity_roles = MANAGE_ROLES.update_identity_roles  # type: ignore[attr-defined]

_SEED_PATH = Path(__file__).resolve().parents[3] / "scripts" / "seed_user_identities.py"
_SEED_SPEC = importlib.util.spec_from_file_location("seed_user_identities_module_for_roles", _SEED_PATH)
assert _SEED_SPEC and _SEED_SPEC.loader  # pragma: no cover - defensive
_SEED_MODULE = importlib.util.module_from_spec(_SEED_SPEC)
_SEED_SPEC.loader.exec_module(_SEED_MODULE)  # type: ignore[arg-type]
seed_user_identity = _SEED_MODULE.seed_user_identity  # type: ignore[attr-defined]


@pytest.fixture()
def database_url(tmp_path: Path) -> str:
    db_path = tmp_path / "roles.db"
    return f"sqlite+pysqlite:///{db_path}"


def _fetch_roles(database_url: str, provider: str, subject: str) -> tuple[str, ...]:
    manager = SessionManager(database_url)
    Base.metadata.create_all(manager.engine)
    try:
        with manager.session_scope() as session:
            repo = SqlAlchemyUserRepository(session)
            record = repo.find_by_oauth_identity(provider, subject)
            assert record is not None
            return record.roles
    finally:
        manager.dispose()


def test_update_identity_roles_adds_scope(database_url: str) -> None:
    seed_user_identity(
        database_url=database_url,
        user_id="user-1",
        provider="google",
        subject="sub-1",
        roles=("support",),
        two_factor_enabled=False,
    )

    added, removed = update_identity_roles(
        database_url=database_url,
        provider="google",
        subject="sub-1",
        add_roles=("scope:kpi:node:binary:node-1",),
    )

    assert added is True
    assert removed is False
    roles = _fetch_roles(database_url, "google", "sub-1")
    assert roles == ("support", "scope:kpi:node:binary:node-1")


def test_update_identity_roles_removes_scope(database_url: str) -> None:
    seed_user_identity(
        database_url=database_url,
        user_id="user-1",
        provider="google",
        subject="sub-1",
        roles=("support", "scope:kpi:node:binary:node-1"),
        two_factor_enabled=False,
    )

    added, removed = update_identity_roles(
        database_url=database_url,
        provider="google",
        subject="sub-1",
        remove_roles=("scope:kpi:node:binary:node-1",),
    )

    assert added is False
    assert removed is True
    roles = _fetch_roles(database_url, "google", "sub-1")
    assert roles == ("support",)


def test_update_identity_roles_raises_when_missing(database_url: str) -> None:
    with pytest.raises(ValueError):
        update_identity_roles(
            database_url=database_url,
            provider="google",
            subject="missing",
            add_roles=("support",),
        )
