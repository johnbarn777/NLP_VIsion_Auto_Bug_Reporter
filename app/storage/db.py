"""Database setup for SQLAlchemy sessions and engine."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Default SQLite database URL; individual components/tests may override
DEFAULT_DB_URL = "sqlite:///./data/app.db"

# Engine and session factory are created lazily so tests can supply custom URLs.
_engine = None
_SessionLocal = None


def init_engine(db_url: str = DEFAULT_DB_URL) -> None:
    """Initialise the global SQLAlchemy engine and session factory."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, class_=Session)


def get_engine() -> "Engine":  # type: ignore[name-defined]
    if _engine is None:
        init_engine()
    return _engine


def get_session() -> Session:
    if _SessionLocal is None:
        init_engine()
    return _SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
