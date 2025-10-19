#!/usr/bin/env python3
"""Seed initial user identities for OAuth authentication."""

from __future__ import annotations

import argparse
import os
from typing import Iterable, Tuple

from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import UserIdentityModel
from aeghash.infrastructure.session import SessionManager


def parse_roles(value: str) -> Tuple[str, ...]:
    roles = tuple(role.strip() for role in value.split(",") if role.strip())
    if not roles:
        raise argparse.ArgumentTypeError("At least one role must be provided.")
    return roles


def seed_user_identity(
    *,
    database_url: str,
    user_id: str,
    provider: str,
    subject: str,
    roles: Iterable[str],
    two_factor_enabled: bool,
) -> bool:
    """Insert a user identity if it does not already exist."""
    manager = SessionManager(database_url)
    Base.metadata.create_all(manager.engine)
    inserted = False
    try:
        with manager.session_scope() as session:
            existing = (
                session.query(UserIdentityModel)
                .filter(
                    UserIdentityModel.provider == provider,
                    UserIdentityModel.subject == subject,
                )
                .one_or_none()
            )
            if existing:
                return False

            session.add(
                UserIdentityModel(
                    user_id=user_id,
                    provider=provider,
                    subject=subject,
                    roles=",".join(roles),
                    two_factor_enabled=two_factor_enabled,
                ),
            )
            inserted = True
    finally:
        manager.dispose()
    return inserted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed user identities for OAuth authentication.")
    parser.add_argument("--user-id", required=True, help="Internal user identifier.")
    parser.add_argument("--provider", required=True, help="OAuth provider key (e.g., google, kakao).")
    parser.add_argument("--subject", required=True, help="Provider-specific subject identifier.")
    parser.add_argument(
        "--roles",
        default="member",
        type=parse_roles,
        help="Comma-separated list of roles (default: member).",
    )
    parser.add_argument(
        "--two-factor-enabled",
        action="store_true",
        help="Mark the identity as having two-factor authentication enabled.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="Database URL (default: DATABASE_URL environment variable).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.database_url:
        parser.error("DATABASE_URL must be provided either via --database-url or environment variable.")

    inserted = seed_user_identity(
        database_url=args.database_url,
        user_id=args.user_id,
        provider=args.provider,
        subject=args.subject,
        roles=args.roles,
        two_factor_enabled=args.two_factor_enabled,
    )
    if inserted:
        print("Seeded user identity successfully.")
    else:
        print("User identity already exists; no action taken.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
