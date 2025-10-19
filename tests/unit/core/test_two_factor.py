import time

import pytest
from cryptography.fernet import Fernet

from aeghash.core.repositories import TwoFactorRecord, TwoFactorRepository
from aeghash.core.two_factor import TwoFactorService
from aeghash.utils import totp


class InMemoryTwoFactorRepository(TwoFactorRepository):
    def __init__(self) -> None:
        self.records: dict[str, TwoFactorRecord] = {}

    def get(self, user_id: str) -> TwoFactorRecord | None:
        return self.records.get(user_id)

    def save(self, record: TwoFactorRecord) -> None:
        self.records[record.user_id] = record

    def disable(self, user_id: str) -> None:
        if user_id in self.records:
            self.records[user_id] = TwoFactorRecord(
                user_id=user_id,
                secret=self.records[user_id].secret,
                enabled=False,
                updated_at=time.time(),
                recovery_codes=self.records[user_id].recovery_codes,
            )


def test_enable_two_factor_generates_secret():
    repo = InMemoryTwoFactorRepository()
    events: list[tuple[str, dict[str, object]]] = []

    def event_hook(name: str, payload: dict[str, object]) -> None:
        events.append((name, dict(payload)))

    service = TwoFactorService(repo, event_hook=event_hook)

    status = service.enable("user-1")

    assert status.enabled is True
    assert status.secret is not None
    assert len(status.recovery_codes) == 5
    assert repo.get("user-1").enabled is True  # type: ignore[union-attr]
    stored = repo.get("user-1")
    assert stored is not None
    assert stored.recovery_codes
    for code in status.recovery_codes:
        assert code not in stored.recovery_codes
    assert events and events[-1][0] == "two_factor.enabled"


def test_verify_two_factor_code():
    repo = InMemoryTwoFactorRepository()
    service = TwoFactorService(repo)
    status = service.enable("user-1")

    code = totp.totp(status.secret)  # type: ignore[arg-type]
    assert service.verify("user-1", code) is True


def test_verify_invalid_code_returns_false():
    repo = InMemoryTwoFactorRepository()
    service = TwoFactorService(repo)
    service.enable("user-1")

    assert service.verify("user-1", "000000") is False


def test_secret_encrypted_when_key_available(monkeypatch):
    repo = InMemoryTwoFactorRepository()
    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("AEGHASH_ENCRYPTION_KEY", key)
    service = TwoFactorService(repo)

    status = service.enable("user-1")
    stored = repo.get("user-1")
    assert stored is not None
    assert stored.secret != status.secret

    code = totp.totp(status.secret)  # type: ignore[arg-type]
    assert service.verify("user-1", code) is True

    monkeypatch.delenv("AEGHASH_ENCRYPTION_KEY", raising=False)


def test_use_recovery_code_consumes_once():
    repo = InMemoryTwoFactorRepository()
    service = TwoFactorService(repo)
    status = service.enable("user-1")
    code = status.recovery_codes[0]

    assert service.use_recovery_code("user-1", code) is True
    assert service.use_recovery_code("user-1", code) is False
    stored = repo.get("user-1")
    assert stored is not None
    assert len(stored.recovery_codes) == 4


def test_disable_emits_event_and_returns_flag():
    repo = InMemoryTwoFactorRepository()
    events: list[tuple[str, dict[str, object]]] = []

    def event_hook(name: str, payload: dict[str, object]) -> None:
        events.append((name, dict(payload)))

    service = TwoFactorService(repo, event_hook=event_hook)
    service.enable("user-1")

    assert service.disable("user-1", actor_id="admin-42") is True
    assert service.disable("user-1") is False
    assert events[-1][0] == "two_factor.disabled"
    assert events[-1][1]["actor_id"] == "admin-42"


def test_verify_without_enabling_raises():
    repo = InMemoryTwoFactorRepository()
    service = TwoFactorService(repo)

    with pytest.raises(ValueError):
        service.verify("user-unknown", "123456")
