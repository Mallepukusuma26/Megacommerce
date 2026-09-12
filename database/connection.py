"""
MegaCommerce Database Connection Manager & Session Lifecycle
SQLAlchemy 2.0 ORM Architecture
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config.settings import settings

# Global Declarative Base
Base = declarative_base()

# SQLAlchemy Engine Singleton
engine = create_engine(
    settings.db.connection_url,
    echo=settings.db.ECHO_SQL,
    future=True,
    connect_args={"check_same_thread": False} if settings.db.DB_TYPE.lower() == "sqlite" else {}
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    future=True
)


def get_db() -> Generator[Session, None, None]:
    """Dependency provider yielding transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates all database tables based on declarative ORM metadata."""
    Base.metadata.create_all(bind=engine)
