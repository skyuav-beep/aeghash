from datetime import UTC, datetime
from decimal import Decimal
import time

import pytest
from fastapi.testclient import TestClient

from aeghash.api.http import create_http_app
from aeghash.application import create_application, shutdown_application
from aeghash.infrastructure import (
    SqlAlchemyPointWalletRepository,
    SqlAlchemySessionRepository,
)
from aeghash.core.point_wallet import PointWalletService
from aeghash.core.repositories import SessionRecord


class StubHashDamClient:
    def __init__(self, *, failures: int = 0) -> None:
        self._failures = failures
        self.calls: list[tuple[str, str, Decimal]] = []

    def request_asset_withdrawal(self, *, coin: str, amount: Decimal):
        if self._failures > 0:
            self._failures -= 1
            raise RuntimeError("HashDam unavailable")
        self.calls.append((coin, amount))
        return type("AssetWithdrawal", (), {"withdraw_id": "hashdam-1", "coin": coin, "amount": amount})()

    def close(self) -> None:  # pragma: no cover - nothing to close
        pass


class StubNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message) -> None:
        self.messages.append(f"{message.subject}: {message.body}")


@pytest.fixture()
def test_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGHASH_DEV_MODE", "1")
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    app = create_application()
    container = app.container
    notifier = StubNotifier()
    container.notifier = notifier
    clients: list[StubHashDamClient] = []

    def hashdam_factory() -> StubHashDamClient:
        client = StubHashDamClient()
        clients.append(client)
        return client

    container.hashdam_client_factory = hashdam_factory

    fastapi_app = create_http_app(app, shutdown_on_exit=False)
    client = TestClient(fastapi_app)
    yield client, container, notifier, clients
    client.close()
    shutdown_application(app)


def _seed_withdrawal(container, *, amount: Decimal, metadata: dict[str, object]):
    with container.session_manager.session_scope() as session:
        repo = SqlAlchemyPointWalletRepository(session)
        service = PointWalletService(repo, clock=lambda: datetime(2025, 1, 1, tzinfo=UTC))
        wallet = service.credit(user_id="user-1", amount=Decimal("100"))
        snapshot = service.request_withdrawal(
            wallet_id=wallet.wallet_id,
            amount=amount,
            requested_by="user-1",
            metadata=metadata,
        )
        return snapshot.request_id, wallet.wallet_id


def _get_withdrawal(container, request_id: str):
    with container.session_manager.session_scope() as session:
        repo = SqlAlchemyPointWalletRepository(session)
        service = PointWalletService(repo, clock=lambda: datetime(2025, 1, 1, tzinfo=UTC))
        return service.get_withdrawal(request_id)


def _seed_session(container, token: str, roles: tuple[str, ...]) -> None:
    with container.session_manager.session_scope() as session:
        repo = SqlAlchemySessionRepository(session)
        repo.create_session(
            SessionRecord(
                token=token,
                user_id="admin-1",
                roles=roles,
                expires_at=time.time() + 3600,
            ),
        )


def test_approve_withdrawal_success(test_client):
    client, container, notifier, clients = test_client
    request_id, _ = _seed_withdrawal(
        container,
        amount=Decimal("30"),
        metadata={"provider": "hashdam", "coin": "PEP"},
    )
    _seed_session(container, "admin-token", ("admin",))

    stage1 = client.post(
        f"/admin/withdrawals/{request_id}/approve",
        headers={"Authorization": "Bearer admin-token"},
        json={"approved_by": "admin-1", "finalize": False},
    )
    assert stage1.status_code == 202
    assert stage1.json()["status"] == "approved_pending"

    response = client.post(
        f"/admin/withdrawals/{request_id}/approve",
        headers={"Authorization": "Bearer admin-token"},
        json={"approved_by": "admin-2", "finalize": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["metadata"]["hashdam_withdraw_id"] == "hashdam-1"
    assert clients and clients[-1].calls == [("PEP", Decimal("30"))]
    stored = _get_withdrawal(container, request_id)
    assert stored.metadata and stored.metadata.get("hashdam_withdraw_id") == "hashdam-1"
    assert not notifier.messages


def test_approve_withdrawal_failure_returns_502(test_client):
    client, container, notifier, clients = test_client

    def failing_factory() -> StubHashDamClient:
        client = StubHashDamClient(failures=5)
        clients.append(client)
        return client

    container.hashdam_client_factory = failing_factory

    request_id, _ = _seed_withdrawal(
        container,
        amount=Decimal("40"),
        metadata={"provider": "hashdam", "coin": "PEP"},
    )
    _seed_session(container, "admin-token", ("admin",))

    client.post(
        f"/admin/withdrawals/{request_id}/approve",
        headers={"Authorization": "Bearer admin-token"},
        json={"approved_by": "admin-1", "finalize": False},
    )

    response = client.post(
        f"/admin/withdrawals/{request_id}/approve",
        headers={"Authorization": "Bearer admin-token"},
        json={"approved_by": "admin-2", "finalize": True},
    )

    assert response.status_code == 502
    assert notifier.messages
    stored = _get_withdrawal(container, request_id)
    assert stored.status == "failed"
