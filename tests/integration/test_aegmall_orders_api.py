from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from aeghash.application import Application, create_application, shutdown_application
from aeghash.api.http import create_http_app


@pytest.fixture()
def test_app(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGHASH_DEV_MODE", "1")
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    app: Application = create_application()
    fastapi_app = create_http_app(app, shutdown_on_exit=False)
    client = TestClient(fastapi_app)
    yield client
    client.close()
    shutdown_application(app)


def _order_payload(idempotency_key: str, total_amount: Decimal = Decimal("200")) -> dict:
    return {
        "order_id": "order-1",
        "user_id": "user-1",
        "total_amount": str(total_amount),
        "pv_amount": "120",
        "channel": "ONLINE",
        "metadata": {"source": "test"},
        "idempotency_key": idempotency_key,
    }


def test_aegmall_order_created_and_duplicate(test_app: TestClient) -> None:
    response = test_app.post("/aegmall/orders", json=_order_payload("idem-1"))
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "created"
    assert data["order_id"] == "order-1"

    duplicate = test_app.post("/aegmall/orders", json=_order_payload("idem-1"))
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"


def test_aegmall_order_conflict_returns_409(test_app: TestClient) -> None:
    response = test_app.post("/aegmall/orders", json=_order_payload("idem-2"))
    assert response.status_code == 201

    conflict_payload = _order_payload("idem-2", total_amount=Decimal("250"))
    response_conflict = test_app.post("/aegmall/orders", json=conflict_payload)
    assert response_conflict.status_code == 409
