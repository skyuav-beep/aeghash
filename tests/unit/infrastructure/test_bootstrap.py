from decimal import Decimal

from aeghash.adapters.hashdam import HashBalance
from aeghash.config import (
    AppSettings,
    HashDamSettings,
    MBlockSettings,
    OAuthProviderSettings,
    OAuthSettings,
    TurnstileSettings,
)
from aeghash.infrastructure.bootstrap import mining_service_scope, wallet_service_scope
from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import MiningBalanceModel, WithdrawalModel, WalletModel
from aeghash.infrastructure.session import SessionManager


class DummyMBlockClient:
    def __init__(self) -> None:
        self.closed = False

    def request_wallet(self):  # type: ignore[override]
        return type("WalletInfo", (), {"address": "0xabc", "wallet_key": "wallet"})

    def get_balance(self, *, address: str, contract: str | None = None):  # type: ignore[override]
        return Decimal("1")

    def transfer_by_wallet_key(self, *, wallet_key: str, to: str, amount: Decimal, contract: str | None = None):
        return type("Receipt", (), {"txid": "tx123", "message": None})

    def transit_by_wallet_key(self, *, wallet_key: str, to: str, amount: Decimal, contract: str, config_override=None):
        return type("Token", (), {"token": "token123", "message": None})

    def close(self) -> None:
        self.closed = True


class DummyHashDamClient:
    def __init__(self) -> None:
        self.closed = False

    def get_hash_balance(self):
        return HashBalance(date="2025-08-15", credit=Decimal("1"), power=Decimal("10"))

    def request_asset_withdrawal(self, *, coin: str, amount: Decimal):
        return type("Withdrawal", (), {"withdraw_id": "wd123", "coin": coin, "amount": amount})

    def close(self) -> None:
        self.closed = True


def _make_app_settings() -> AppSettings:
    oauth = OAuthSettings(
        google=OAuthProviderSettings(client_id="g", client_secret="gs", redirect_uri="https://redirect"),
        kakao=OAuthProviderSettings(client_id="k", client_secret="ks", redirect_uri="https://redirect"),
        apple=OAuthProviderSettings(client_id="a", client_secret="as", redirect_uri="https://redirect"),
    )
    return AppSettings(
        hashdam=HashDamSettings(),
        mblock=MBlockSettings(base_url="http://mock", api_key="key"),
        oauth=oauth,
        turnstile=TurnstileSettings(secret_key="turnstile"),
        database_url="sqlite+pysqlite:///:memory:",
        secret_key="secret",
    )


def test_wallet_service_scope_manages_client_and_session():
    app_settings = _make_app_settings()

    manager = SessionManager(app_settings.database_url)
    Base.metadata.create_all(manager.engine)

    def client_factory() -> DummyMBlockClient:
        return DummyMBlockClient()

    with wallet_service_scope(manager, client_factory, app_settings) as service:
        info = service.create_wallet(user_id="user")
        assert info.wallet_key == "wallet"

    with manager.session_scope() as session:
        assert session.query(WalletModel).count() == 1

    manager.dispose()


def test_mining_service_scope():
    app_settings = _make_app_settings()

    manager = SessionManager(app_settings.database_url)
    Base.metadata.create_all(manager.engine)

    def client_factory() -> DummyHashDamClient:
        return DummyHashDamClient()

    with mining_service_scope(manager, client_factory, app_settings) as service:
        balance = service.get_balance(user_id="user")
        assert balance.credit == Decimal("1")
        service.request_withdrawal(user_id="user", coin="PEP", amount=Decimal("1"))

    with manager.session_scope() as session:
        assert session.query(MiningBalanceModel).filter_by(user_id="user").one().credit == Decimal("1")
        assert session.query(WithdrawalModel).filter_by(user_id="user").one().status == "submitted"

    manager.dispose()
