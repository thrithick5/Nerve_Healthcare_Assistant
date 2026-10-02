"""Startup migration runner.

Why this exists
---------------
On Render, ``fromDatabase: {property: connectionString}`` injects the
database's *internal* URL. That hostname only resolves from services in the
same workspace **and region**. When it does not resolve, alembic fails with:

    psycopg2.OperationalError: could not translate host name "dpg-..." to address

The previous Dockerfile chained ``alembic upgrade head && uvicorn ...``, so a
DNS failure meant uvicorn never started and Render crash-looped the service.

This module therefore:
  1. waits (bounded, exponential backoff) for the database to accept a
     connection, which absorbs cold starts and slow DNS propagation, and
  2. runs migrations when possible, but **never** exits non-zero, so the API
     always boots and can recover once the database becomes reachable.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.url_utils import (  # noqa: E402
    normalize_database_url,
    redact_database_url,
)

logger = logging.getLogger("startup.migrations")

# Bounded wait: long enough to absorb a cold-started database, short enough
# that a genuinely unreachable host cannot stall the Render deploy window.
# Worst case here is 2+4+8+10+10 = ~34s.
DEFAULT_ATTEMPTS = 6
DEFAULT_BASE_DELAY = 2.0
DEFAULT_MAX_DELAY = 10.0
CONNECT_TIMEOUT_SECONDS = 5.0


def probe_database(database_url: str, timeout: int = CONNECT_TIMEOUT_SECONDS) -> None:
    """Raise if the database cannot be reached. Performs a real connect."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    engine_kwargs = {"poolclass": NullPool}
    if database_url.startswith("postgresql://"):
        # Bound the TCP connect so an unreachable host cannot hang startup.
        # NOTE: SQLAlchemy rejects connect_args=None, so only pass it when set.
        engine_kwargs["connect_args"] = {"connect_timeout": int(timeout)}

    engine = create_engine(database_url, **engine_kwargs)
    try:
        with engine.connect():
            pass
    finally:
        engine.dispose()


def wait_for_database(
    database_url: str,
    attempts: int = DEFAULT_ATTEMPTS,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    probe: Callable[[str], None] = probe_database,
    sleep: Callable[[float], None] = time.sleep,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Retry ``probe`` until it succeeds or attempts are exhausted.

    Never raises: any connection failure is treated as "not ready yet".
    Does not sleep after the final attempt.
    """
    if logger is None:
        logger = logging.getLogger("startup.migrations")

    if attempts < 1:
        logger.error("database probe skipped: attempts=%s", attempts)
        return False

    delay = base_delay
    last_error: Optional[BaseException] = None

    for attempt in range(1, attempts + 1):
        try:
            probe(database_url)
            logger.info("database reachable on attempt %s/%s", attempt, attempts)
            return True
        except Exception as exc:  # noqa: BLE001 - boot must survive any connection error
            last_error = exc
            if attempt >= attempts:
                break
            logger.warning(
                "database not reachable (attempt %s/%s): %s", attempt, attempts, exc
            )
            sleep(delay)
            delay = min(delay * 2, max_delay)

    logger.error("database unreachable after %s attempt(s): %s", attempts, last_error)
    return False


def run_alembic_upgrade(
    cwd: str,
    runner=subprocess.run,
    python_executable: Optional[str] = None,
    log_output: bool = False,
    logger: Optional[logging.Logger] = None,
) -> int:
    """Run ``alembic upgrade head`` in ``cwd``; return its exit code.

    Alembic reads DATABASE_URL from the environment, so it must be inherited
    rather than passed as an argument. Output is captured so the password in a
    Render-style URL is never echoed into logs; pass ``log_output=True`` when
    debugging locally.
    """
    python_executable = python_executable or sys.executable
    completed = runner(
        [python_executable, "-m", "alembic", "upgrade", "head"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if logger is not None and completed.returncode != 0:
        if log_output:
            logger.error("alembic output:\n%s\n%s", completed.stdout, completed.stderr)
        else:
            logger.error(
                "alembic failed (exit %s). Re-run locally with log_output=True "
                "for the full traceback.",
                completed.returncode,
            )
    return completed.returncode


def main(
    env=None,
    cwd: Optional[str] = None,
    probe: Callable[[str], None] = probe_database,
    runner=subprocess.run,
    sleep: Callable[[float], None] = time.sleep,
    attempts: int = DEFAULT_ATTEMPTS,
    logger: Optional[logging.Logger] = None,
    python_executable: Optional[str] = None,
) -> int:
    """Apply migrations if the database is reachable.

    Returns 0 unconditionally so the container always proceeds to start the
    API server. A database outage must not take the whole service down.
    """
    if logger is None:
        logger = logging.getLogger("startup.migrations")
    env = os.environ if env is None else env
    cwd = os.getcwd() if cwd is None else cwd

    database_url = normalize_database_url(env.get("DATABASE_URL"))
    logger.info("running startup migrations against %s", redact_database_url(database_url))

    if not wait_for_database(
        database_url, attempts=attempts, probe=probe, sleep=sleep, logger=logger
    ):
        logger.error(
            "skipping migrations: database unreachable. The API will start and "
            "will connect once the database becomes reachable."
        )
        return 0

    return_code = run_alembic_upgrade(
        cwd=cwd,
        runner=runner,
        python_executable=python_executable,
        logger=logger,
    )
    if return_code == 0:
        logger.info("migrations applied successfully")
    else:
        logger.error(
            "alembic upgrade head failed with exit code %s; "
            "starting the API anyway",
            return_code,
        )
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s"
    )
    sys.exit(main())
