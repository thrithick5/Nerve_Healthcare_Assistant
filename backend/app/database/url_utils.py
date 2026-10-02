"""Database URL helpers.

Kept dependency-free and side-effect free so it can be imported from
`alembic/env.py`, `app/database/connection.py` and startup scripts alike
without triggering engine creation or any other import-time work.
"""
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

DEFAULT_DATABASE_URL = "sqlite:///./data/healthcare.db"

_LEGACY_POSTGRES_PREFIX = "postgres://"
_MODERN_POSTGRES_PREFIX = "postgresql://"


def normalize_database_url(database_url: str | None) -> str:
    """Return a SQLAlchemy-usable database URL.

    Rewrites the deprecated ``postgres://`` scheme to ``postgresql://``
    (Render and Heroku still emit the legacy form) and falls back to the
    local SQLite default when no usable value is configured. Only the scheme
    is rewritten, so percent-encoded credentials are preserved verbatim.
    """
    if database_url is None:
        return DEFAULT_DATABASE_URL
    cleaned = database_url.strip()
    if not cleaned:
        return DEFAULT_DATABASE_URL
    if cleaned.startswith(_LEGACY_POSTGRES_PREFIX):
        return _MODERN_POSTGRES_PREFIX + cleaned[len(_LEGACY_POSTGRES_PREFIX):]
    return cleaned


def is_sqlite_url(database_url: str | None) -> bool:
    if not database_url:
        return False
    return normalize_database_url(database_url).startswith("sqlite")


def describe_host(database_url: str | None) -> str | None:
    """Extract just the hostname, for diagnostics. ``None`` when absent."""
    if not database_url:
        return None
    try:
        parts = urlsplit(normalize_database_url(database_url))
    except ValueError:
        return None
    return parts.hostname or None


def redact_database_url(database_url: str | None) -> str:
    """Return a log-safe URL with any embedded password replaced by ``***``.

    Database URLs are logged during startup, so credentials must never be
    written to stdout (Render captures container logs).
    """
    normalized = normalize_database_url(database_url)
    try:
        parts = urlsplit(normalized)
    except ValueError:
        return "<unparsable database url>"
    if not parts.scheme or not parts.netloc or "@" not in parts.netloc:
        # No credentials embedded, so there is nothing to redact.
        return normalized
    userinfo, _, hostinfo = parts.netloc.rpartition("@")
    if ":" not in userinfo:
        # Passwordless URL: nothing to mask.
        return normalized
    user = userinfo.split(":", 1)[0]
    return urlunsplit(
        (parts.scheme, f"{user}:***@{hostinfo}", parts.path, parts.query, parts.fragment)
    )
