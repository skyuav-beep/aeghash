"""Application bootstrap helpers for service wiring."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
import logging
from typing import Callable, Iterator, Optional

from aeghash.adapters.hashdam import HashDamClient, HashDamHTTPTransport
from aeghash.adapters.mblock import MBlockClient, MBlockHTTPTransport
from aeghash.adapters.turnstile import TurnstileClient
from aeghash.adapters.oauth import (
    AppleOAuthClient,
    GoogleOAuthClient,
    KakaoOAuthClient,
    OAuthHTTPTransport,
    OAuthTransport,
)
from aeghash.config import AppSettings, is_dev_mode
from aeghash.core.auth_service import AuthEventHook, AuthService
from aeghash.core.bonus_pipeline import BonusPipeline
from aeghash.core.commerce_service import AegmallOrderService
from aeghash.core.mining_service import MiningService
from aeghash.core.mining_workflow import MiningWithdrawalOrchestrator, WithdrawalExecutionError
from aeghash.core.wallet_service import WalletService
from aeghash.core.point_wallet import PointWalletService
from aeghash.core.withdrawal_workflow import WithdrawalWorkflowService
from aeghash.core.turnstile import TurnstileVerifier
from aeghash.infrastructure.audit import LoginAuditLogger
from aeghash.infrastructure.repositories import (
    SqlAlchemyBonusRepository,
    SqlAlchemyIdempotencyRepository,
    SqlAlchemyMiningRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyWalletRepository,
    SqlAlchemyPointWalletRepository,
    SqlAlchemyWithdrawalAuditRepository,
)
from aeghash.infrastructure.session import SessionManager
from aeghash.utils import Notifier
from aeghash.utils.webhook_notifier import WebhookNotifier


@dataclass(slots=True)
class ServiceContainer:
    """Application service container."""

    settings: AppSettings
    session_manager: SessionManager
    auth_service: AuthService
    audit_logger: Optional[LoginAuditLogger] = None
    turnstile_client: Optional[TurnstileClient] = None
    turnstile_verifier: Optional[TurnstileVerifier] = None
    notifier: Optional[Notifier] = None
    mblock_client_factory: Callable[[], MBlockClient] | None = None
    hashdam_client_factory: Callable[[], HashDamClient] | None = None
    event_hook: AuthEventHook | None = None


@contextmanager
def wallet_service_scope(
    session_manager: SessionManager,
    client_factory: Callable[[], MBlockClient],
    settings: AppSettings,
    *,
    notifier: Notifier | None = None,
) -> Iterator[WalletService]:
    """Provide a WalletService instance inside a managed session scope."""

    with session_manager.session_scope() as session:
        client = client_factory()
        repo = SqlAlchemyWalletRepository(session)
        try:
            yield WalletService(client=client, settings=settings.mblock, repository=repo, notifier=notifier)
        finally:
            client.close()


@contextmanager
def mining_service_scope(
    session_manager: SessionManager,
    client_factory: Callable[[], HashDamClient],
    settings: AppSettings,
    *,
    notifier: Notifier | None = None,
) -> Iterator[MiningService]:
    """Provide a MiningService instance inside a managed session scope."""

    with session_manager.session_scope() as session:
        client = client_factory()
        repo = SqlAlchemyMiningRepository(session)
        try:
            yield MiningService(client=client, repository=repo, notifier=notifier)
        finally:
            client.close()


@contextmanager
def aegmall_order_service_scope(
    session_manager: SessionManager,
) -> Iterator[AegmallOrderService]:
    """Provide an AegmallOrderService instance inside a managed session scope."""

    with session_manager.session_scope() as session:
        order_repo = SqlAlchemyOrderRepository(session)
        idempotency_repo = SqlAlchemyIdempotencyRepository(session)
        bonus_repo = SqlAlchemyBonusRepository(session)
        organization_repo = SqlAlchemyOrganizationRepository(session)
        pipeline = BonusPipeline(organization_repo, bonus_repo)
        yield AegmallOrderService(
            order_repository=order_repo,
            idempotency_repository=idempotency_repo,
            bonus_pipeline=pipeline,
        )


@contextmanager
def withdrawal_workflow_scope(
    session_manager: SessionManager,
    *,
    mining_client_factory: Callable[[], HashDamClient],
    notifier: Notifier | None = None,
) -> Iterator[WithdrawalWorkflowService]:
    """Provide a withdrawal workflow service coupled with mining orchestrator."""

    with session_manager.session_scope() as session:
        wallet_repo = SqlAlchemyPointWalletRepository(session)
        audit_repo = SqlAlchemyWithdrawalAuditRepository(session)
        mining_repo = SqlAlchemyMiningRepository(session)

        mining_client = mining_client_factory()
        try:
            wallet_service = PointWalletService(wallet_repo)
            mining_service = MiningService(
                client=mining_client,
                repository=mining_repo,
                notifier=notifier,
            )
            orchestrator = MiningWithdrawalOrchestrator(mining_service, wallet_service, notifier=notifier)
            workflow = WithdrawalWorkflowService(
                wallet_service,
                audit_repository=audit_repo,
                mining_orchestrator=orchestrator,
                two_step_required=True,
            )
            try:
                yield workflow
            except WithdrawalExecutionError:
                session.commit()
                raise
        finally:
            mining_client.close()


def create_auth_service(
    settings: AppSettings,
    *,
    event_hook: AuthEventHook | None = None,
    logger: logging.Logger | None = None,
    transport_factory: Callable[[str], OAuthTransport] | None = None,
) -> AuthService:
    """Instantiate AuthService with HTTP transports for each provider."""
    factory = transport_factory or (lambda _provider: OAuthHTTPTransport())
    clients = [
        GoogleOAuthClient(transport=factory("google"), settings=settings.oauth.google),
        KakaoOAuthClient(transport=factory("kakao"), settings=settings.oauth.kakao),
        AppleOAuthClient(transport=factory("apple"), settings=settings.oauth.apple),
    ]
    return AuthService(
        {client.provider_name: client for client in clients},
        event_hook=event_hook,
        logger=logger,
    )


def bootstrap_services(
    settings: AppSettings,
    *,
    event_hook: AuthEventHook | None = None,
    logger: logging.Logger | None = None,
    transport_factory: Callable[[str], OAuthTransport] | None = None,
    notifier: Notifier | None = None,
) -> ServiceContainer:
    """Create core service container for application startup."""
    session_manager = SessionManager(settings.database_url)
    auth_service = create_auth_service(
        settings,
        event_hook=event_hook,
        logger=logger,
        transport_factory=transport_factory,
    )
    if is_dev_mode():
        turnstile_client: Optional[TurnstileClient] = None
        turnstile_verifier: Optional[TurnstileVerifier] = None
    else:
        turnstile_client = TurnstileClient(secret_key=settings.turnstile.secret_key)
        turnstile_verifier = TurnstileVerifier(turnstile_client)
    resolved_notifier = notifier
    if resolved_notifier is None:
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if webhook_url:
            resolved_notifier = WebhookNotifier(url=webhook_url)
    def make_mblock_client() -> MBlockClient:
        transport = MBlockHTTPTransport(
            base_url=settings.mblock.base_url,
            api_key=settings.mblock.api_key,
        )
        return MBlockClient(transport)

    def make_hashdam_client() -> HashDamClient:
        transport = HashDamHTTPTransport(
            base_url=settings.hashdam.base_url,
            api_key=settings.hashdam.api_key,
        )
        return HashDamClient(transport)
    return ServiceContainer(
        settings=settings,
        session_manager=session_manager,
        auth_service=auth_service,
        turnstile_client=turnstile_client,
        turnstile_verifier=turnstile_verifier,
        notifier=resolved_notifier,
        mblock_client_factory=make_mblock_client,
        hashdam_client_factory=make_hashdam_client,
        event_hook=event_hook,
    )


def shutdown_services(container: ServiceContainer) -> None:
    """Gracefully dispose service container resources."""
    container.auth_service.close()
    container.session_manager.dispose()
    if container.turnstile_client:
        container.turnstile_client.close()
