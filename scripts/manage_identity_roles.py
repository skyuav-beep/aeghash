#!/usr/bin/env python3
"""Utility for updating roles/scopes on existing user identities."""

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


def update_identity_roles(
    *,
    database_url: str,
    provider: str,
    subject: str,
    add_roles: Iterable[str] = (),
    remove_roles: Iterable[str] = (),
) -> tuple[bool, bool]:
    """Update an existing user identity by adding/removing roles."""
    manager = SessionManager(database_url)
    Base.metadata.create_all(manager.engine)
    try:
        with manager.session_scope() as session:
            identity = (
                session.query(UserIdentityModel)
                .filter(
                    UserIdentityModel.provider == provider,
                    UserIdentityModel.subject == subject,
                )
                .one_or_none()
            )
            if identity is None:
                raise ValueError(f"Identity {provider}:{subject} not found.")

            existing = [role for role in identity.roles.split(",") if role]
            original_set = set(existing)
            roles = list(existing)

            added = False
            for role in add_roles:
                if role not in original_set:
                    roles.append(role)
                    original_set.add(role)
                    added = True

            removed = False
            if remove_roles:
                to_remove = set(remove_roles)
                if to_remove:
                    new_roles = [role for role in roles if role not in to_remove]
                    removed = len(new_roles) != len(roles)
                    roles = new_roles

            if added or removed:
                identity.roles = ",".join(roles)
            return added, removed
    finally:
        manager.dispose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update roles/scopes on an existing user identity.",
    )
    parser.add_argument("--provider", required=True, help="OAuth provider key (e.g., google, kakao).")
    parser.add_argument("--subject", required=True, help="Provider-specific subject identifier.")
    parser.add_argument(
        "--add-roles",
        type=parse_roles,
        default=(),
        help="Comma-separated roles/scopes to append (duplicates ignored).",
    )
    parser.add_argument(
        "--remove-roles",
        type=parse_roles,
        default=(),
        help="Comma-separated roles/scopes to remove.",
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

    try:
        added, removed = update_identity_roles(
            database_url=args.database_url,
            provider=args.provider,
            subject=args.subject,
            add_roles=args.add_roles,
            remove_roles=args.remove_roles,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if added or removed:
        print("Updated roles:", "added" if added else "", "removed" if removed else "")
    else:
        print("Roles unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
