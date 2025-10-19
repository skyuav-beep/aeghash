import importlib.util
from pathlib import Path

import pytest

from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import SqlAlchemyUserRepository
from aeghash.infrastructure.session import SessionManager

_MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "seed_user_identities.py"
_SPEC = importlib.util.spec_from_file_location("seed_user_identities_module", _MODULE_PATH)
assert _SPEC and _SPEC.loader  # pragma: no cover - defensive
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)  # type: ignore[arg-type]

seed_user_identity = _MODULE.seed_user_identity  # type: ignore[attr-defined]


@pytest.fixture()
def database_url(tmp_path: Path) -> str:
    db_path = tmp_path / "test.db"
    return f"sqlite+pysqlite:///{db_path}"


def test_seed_user_identity_inserts_when_missing(database_url: str) -> None:
    inserted = seed_user_identity(
        database_url=database_url,
        user_id="user-1",
        provider="google",
        subject="subject-1",
        roles=("member", "admin"),
        two_factor_enabled=True,
    )
    assert inserted is True

    manager = SessionManager(database_url)
    Base.metadata.create_all(manager.engine)
    with manager.session_scope() as session:
        repo = SqlAlchemyUserRepository(session)
        record = repo.find_by_oauth_identity("google", "subject-1")
    manager.dispose()

    assert record is not None
    assert record.roles == ("member", "admin")
    assert record.two_factor_enabled is True


def test_seed_user_identity_returns_false_when_existing(database_url: str) -> None:
    seed_user_identity(
        database_url=database_url,
        user_id="user-1",
        provider="google",
        subject="subject-1",
        roles=("member",),
        two_factor_enabled=False,
    )
    inserted = seed_user_identity(
        database_url=database_url,
        user_id="user-2",
        provider="google",
        subject="subject-1",
        roles=("admin",),
        two_factor_enabled=True,
    )
    assert inserted is False
