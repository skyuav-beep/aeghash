"""Session management utilities for SQLAlchemy."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Tuple

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from aeghash.infrastructure.database import create_engine_and_session


class SessionManager:
    """Manage engine and session factory with context support."""

    def __init__(self, database_url: str) -> None:
        self.engine, self._session_factory = create_engine_and_session(database_url)

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()


def init_engine_and_session(database_url: str) -> Tuple[Engine, sessionmaker]:
    """Convenience wrapper for legacy usage."""
    return create_engine_and_session(database_url)
