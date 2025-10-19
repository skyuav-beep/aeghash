#!/usr/bin/env python3
"""Command-line helper for exercising the OAuth authentication flow."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Sequence

from aeghash.application import Application, create_application, shutdown_application


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Authenticate via configured OAuth provider.")
    parser.add_argument("provider", help="OAuth provider key (e.g., google, kakao, apple)")
    parser.add_argument("code", help="Authorization code obtained from the provider callback")
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Print collected authentication metrics after execution.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO).",
    )
    parser.add_argument(
        "--no-logging-exporter",
        action="store_true",
        help="Disable the default logging metrics exporter.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s %(name)s - %(message)s")

    app: Application | None = None
    try:
        app = create_application(enable_logging_exporter=not args.no_logging_exporter)
        result = app.container.auth_service.authenticate(provider=args.provider, code=args.code)
        print(
            f"Authenticated with provider '{result.profile.provider}' "
            f"for subject '{result.profile.subject}'.",
        )
        if args.metrics:
            snapshot = app.metrics.snapshot()
            print(json.dumps(snapshot, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - error path
        logging.exception("Authentication failed", exc_info=exc)
        return 1
    finally:
        if app is not None:
            shutdown_application(app)


if __name__ == "__main__":
    sys.exit(main())
