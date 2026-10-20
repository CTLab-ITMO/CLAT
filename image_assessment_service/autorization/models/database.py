import os
from contextlib import contextmanager

from image_assessment_service.config import get_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine_instance = None
_session_maker_instance = None


def init_database():
    global _engine_instance
    global _session_maker_instance

    _ensure_not_inited()

    sqlalchemy_database_url = get_config().postgres.get_database_url()

    _engine_instance = _create_engine(sqlalchemy_database_url)
    _session_maker_instance = sessionmaker(
        autoflush=False, autocommit=False, bind=_engine_instance
    )


def _ensure_not_inited():
    if _engine_instance is not None:
        raise RuntimeError("Database engine is already created")
    if _session_maker_instance is not None:
        raise RuntimeError("Database session maker is already created")


def _create_engine(sqlalchemy_database_url):
    return create_engine(
        sqlalchemy_database_url,
        pool_pre_ping=True,  # Checks connection is alive before use
        pool_recycle=30,  # Recycle connections after 1 hour
        max_overflow=80,
        pool_size=10,
    )


def get_engine():
    return _engine_instance


def get_db():
    db = _session_maker_instance()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    yield from get_db()
