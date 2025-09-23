from __future__ import annotations

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure repo root is on sys.path so "agents" is importable 
REPO_ROOT: Path | None = None
for p in Path(__file__).resolve().parents:
    if (p / "agents").is_dir():
        REPO_ROOT = p
        break

if REPO_ROOT and str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Now imports work regardless of cwd
from agents.applicant_evaluator.app.db.base import Base  # noqa: E402
from agents.applicant_evaluator.app.db import models  # noqa: F401,E402 (ensures models are imported)
from agents.applicant_evaluator.app.core.config import settings  # noqa: E402

# Alembic config
config = context.config

# Logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata


# DATABASE URL RESOLUTION
def get_url() -> str:
    """Resolve DB URL with clear precedence."""
    # 1. Explicit env var DATABASE_URL
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # 2. sqlalchemy.url from alembic.ini
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url

    # 3. Build from settings + overrides
    s = settings()
    host = os.getenv("POSTGRES_HOST", s.POSTGRES_HOST)
    port = os.getenv("POSTGRES_PORT", str(s.POSTGRES_PORT))
    user = os.getenv("POSTGRES_USER", s.POSTGRES_USER)
    pw   = os.getenv("POSTGRES_PASSWORD", s.POSTGRES_PASSWORD)
    db   = os.getenv("POSTGRES_DB", s.POSTGRES_DB)
    return f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"


DATABASE_URL = get_url()

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

