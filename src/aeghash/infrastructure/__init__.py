"""Infrastructure utilities including database repositories and service wiring."""

from .audit import LoginAuditLogger
from .bootstrap import (
    ServiceContainer,
    bootstrap_services,
    create_auth_service,
    mining_service_scope,
    withdrawal_workflow_scope,
    shutdown_services,
    wallet_service_scope,
)
from .database import Base, create_engine_and_session
from .repositories import (
    SqlAlchemyLoginAuditRepository,
    SqlAlchemyMiningRepository,
    SqlAlchemyPointWalletRepository,
    SqlAlchemyRiskRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyBonusRepository,
    SqlAlchemyWithdrawalAuditRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyIdempotencyRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyTwoFactorRepository,
    SqlAlchemyUserAccountRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyWalletRepository,
)
from .session import SessionManager

__all__ = [
    "Base",
    "create_engine_and_session",
    "SessionManager",
    "SqlAlchemyWalletRepository",
    "SqlAlchemyMiningRepository",
    "SqlAlchemyPointWalletRepository",
    "SqlAlchemyRiskRepository",
    "SqlAlchemyOrganizationRepository",
    "SqlAlchemyBonusRepository",
    "SqlAlchemyWithdrawalAuditRepository",
    "SqlAlchemyOrderRepository",
    "SqlAlchemyIdempotencyRepository",
    "SqlAlchemyLoginAuditRepository",
    "SqlAlchemyTwoFactorRepository",
    "SqlAlchemySessionRepository",
    "SqlAlchemyUserAccountRepository",
    "SqlAlchemyUserRepository",
    "wallet_service_scope",
    "mining_service_scope",
    "create_auth_service",
    "bootstrap_services",
    "shutdown_services",
    "ServiceContainer",
    "LoginAuditLogger",
    "withdrawal_workflow_scope",
]
