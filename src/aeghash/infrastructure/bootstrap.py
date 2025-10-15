"""Application bootstrap helpers for dependency wiring."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator

from aeghash.adapters.hashdam import HashDamClient
from aeghash.adapters.mblock import MBlockClient
from aeghash.config import AppSettings
from aeghash.core.mining_service import MiningService
from aeghash.core.wallet_service import WalletService
from aeghash.infrastructure.repositories import SqlAlchemyMiningRepository, SqlAlchemyWalletRepository
from aeghash.infrastructure.session import SessionManager


@contextmanager
def wallet_service_scope(
    session_manager: SessionManager,
    client_factory: Callable[[], MBlockClient],
    settings: AppSettings,
) -> Iterator[WalletService]:
    """Provide a WalletService instance inside a managed session scope."""

    with session_manager.session_scope() as session:
        client = client_factory()
        repo = SqlAlchemyWalletRepository(session)
        try:
            yield WalletService(client=client, settings=settings.mblock, repository=repo)
        finally:
            client.close()


@contextmanager
def mining_service_scope(
    session_manager: SessionManager,
    client_factory: Callable[[], HashDamClient],
    settings: AppSettings,
) -> Iterator[MiningService]:
    """Provide a MiningService instance inside a managed session scope."""

    with session_manager.session_scope() as session:
        client = client_factory()
        repo = SqlAlchemyMiningRepository(session)
        try:
            yield MiningService(client=client, repository=repo)
        finally:
            client.close()
