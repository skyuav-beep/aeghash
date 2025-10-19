"""Database utilities for SQLAlchemy integration."""

from __future__ import annotations

from typing import Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def create_engine_and_session(url: str) -> Tuple[Engine, sessionmaker]:
    """Create SQLAlchemy engine and session factory."""
    engine = create_engine(url, future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return engine, SessionLocal
