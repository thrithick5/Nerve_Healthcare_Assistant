from logging.config import fileConfig
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.database.connection import Base
from app.database import models
from app.database.url_utils import DEFAULT_DATABASE_URL, normalize_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
# Percent signs are ConfigParser interpolation syntax; escape them so
# URL-encoded credentials (common on Render) are not corrupted.
config.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
