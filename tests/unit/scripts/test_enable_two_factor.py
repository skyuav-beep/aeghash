import importlib.util
from pathlib import Path

import pytest

from aeghash.infrastructure.session import SessionManager
from aeghash.infrastructure.repositories import SqlAlchemyTwoFactorRepository
from aeghash.core.two_factor import TwoFactorService

_MODULE_PATH = Path(__file__).resolve().parents[3] / "scripts" / "enable_two_factor.py"
_SPEC = importlib.util.spec_from_file_location("enable_two_factor_module", _MODULE_PATH)
assert _SPEC and _SPEC.loader  # pragma: no cover - defensive
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)  # type: ignore[arg-type]

enable_two_factor = _MODULE.enable_two_factor  # type: ignore[attr-defined]
generate_otpauth_uri = _MODULE.generate_otpauth_uri  # type: ignore[attr-defined]


@pytest.fixture()
def database_url(tmp_path: Path) -> str:
    db_path = tmp_path / "two_factor.db"
    return f"sqlite+pysqlite:///{db_path}"


def test_enable_two_factor_generates_secret_and_uri(database_url: str) -> None:
    secret, otpauth = enable_two_factor(
        database_url=database_url,
        user_id="user-1",
        issuer="AEG Hash",
        label="Demo",
    )

    assert secret
    assert otpauth.startswith("otpauth://totp/AEG%20Hash:Demo?")

    manager = SessionManager(database_url)
    with manager.session_scope() as session:
        repo = SqlAlchemyTwoFactorRepository(session)
        service = TwoFactorService(repo)
        assert service.is_enabled("user-1") is True
    manager.dispose()


def test_generate_otpauth_uri_defaults(database_url: str) -> None:
    secret, otpauth = enable_two_factor(
        database_url=database_url,
        user_id="user-2",
        issuer=None,
        label=None,
    )

    assert otpauth.startswith("otpauth://totp/user-2?")
    assert f"secret={secret}" in otpauth
