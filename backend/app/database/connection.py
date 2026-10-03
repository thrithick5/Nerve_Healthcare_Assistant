import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from app.database.url_utils import (
    DEFAULT_DATABASE_URL,
    describe_host,
    is_sqlite_url,
    normalize_database_url,
)

logger = logging.getLogger("app.database")

DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
is_sqlite = is_sqlite_url(DATABASE_URL)

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, echo=False, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> bool:
    """Create any missing tables.

    Returns True on success. A database outage must not prevent the API from
    booting, so connection errors are logged and reported instead of raised:
    SQLAlchemy's pool_pre_ping will reconnect on the next request once the
    database is reachable again.
    """
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except SQLAlchemyError as exc:
        logger.error(
            "database schema initialization failed for host %r: %s",
            describe_host(DATABASE_URL),
            exc,
        )
        return False


def check_database_reachable() -> bool:
    """Cheap reachability probe for the health endpoint.

    Kept synchronous and side-effect free; callers should run it in a worker
    thread so a hanging database cannot stall the event loop.
    """
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return True
    except SQLAlchemyError as exc:
        logger.warning("database health probe failed: %s", exc)
        return False
