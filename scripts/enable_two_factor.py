#!/usr/bin/env python3
"""Enable TOTP-based two-factor authentication for a user."""

from __future__ import annotations

import argparse
import os
from urllib.parse import quote

from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import SqlAlchemyTwoFactorRepository
from aeghash.infrastructure.session import SessionManager
from aeghash.core.two_factor import TwoFactorService


def generate_otpauth_uri(*, secret: str, user_id: str, issuer: str | None = None, label: str | None = None) -> str:
    """Build an otpauth URI for QR-code provisioning."""
    account_label = label or user_id
    if issuer:
        prefix = f"{quote(issuer)}:{quote(account_label)}"
    else:
        prefix = quote(account_label)
    params = [f"secret={secret}"]
    if issuer:
        params.append(f"issuer={quote(issuer)}")
    return f"otpauth://totp/{prefix}?{'&'.join(params)}"


def enable_two_factor(
    *,
    database_url: str,
    user_id: str,
    issuer: str | None = None,
    label: str | None = None,
) -> tuple[str, str, tuple[str, ...]]:
    """Persist a new TOTP secret for a user and return (secret, otpauth_uri, recovery_codes)."""
    manager = SessionManager(database_url)
    Base.metadata.create_all(manager.engine)
    try:
        with manager.session_scope() as session:
            repo = SqlAlchemyTwoFactorRepository(session)
            service = TwoFactorService(repo)
            status = service.enable(user_id)
            otpauth = generate_otpauth_uri(secret=status.secret or "", user_id=user_id, issuer=issuer, label=label)
            return status.secret or "", otpauth, status.recovery_codes
    finally:
        manager.dispose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enable two-factor authentication for a user.")
    parser.add_argument("--user-id", required=True, help="Internal user identifier (matches user_identities.user_id).")
    parser.add_argument("--issuer", help="Issuer name for authenticator apps (e.g., AEG Hash).")
    parser.add_argument("--label", help="Account label override for otpauth URI (defaults to user-id).")
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

    secret, otpauth, recovery_codes = enable_two_factor(
        database_url=args.database_url,
        user_id=args.user_id,
        issuer=args.issuer,
        label=args.label,
    )
    if not secret:
        parser.error("Failed to generate two-factor secret.")

    print("Two-factor authentication enabled.")
    print(f"Secret: {secret}")
    print(f"otpauth URI: {otpauth}")
    print("Scan the otpauth URI with your authenticator app.")
    if recovery_codes:
        print("Recovery codes (store securely, single-use each):")
        for code in recovery_codes:
            print(f"  - {code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
