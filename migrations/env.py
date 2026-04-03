import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from app.config import settings
from app.database import Base
from app.models import financial_record, role, user  # noqa: F401

config = context.config
# Use MIGRATION_DATABASE_URL when set (required if DATABASE_URL points at
# Supabase's transaction pooler on port 6543, which does not support DDL).
database_url = settings.sync_migration_url
# Alembic uses ConfigParser internally, so literal '%' in URL-encoded passwords
# must be escaped when writing into config options.
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

# Log which URL is being used (host only, no credentials)
try:
    from urllib.parse import urlparse as _urlparse
    _parsed = _urlparse(database_url)
    print(f"[Alembic] Connecting to {_parsed.hostname}:{_parsed.port}/{_parsed.path.lstrip('/')}", file=sys.stderr)
except Exception:
    pass
print(f"[Alembic] Attempting database connection with 10s timeout...", file=sys.stderr)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = database_url

    try:
        # For psycopg2, add connect_timeout to the configuration
        # This prevents indefinite hangs on unreachable databases
        configuration["sqlalchemy.connect_args"] = {"connect_timeout": 10}
        
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            # Test connectivity
            connection.execute(text("SELECT 1"))
            print("[Alembic] Database connection successful!", file=sys.stderr)
            
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()
            print("[Alembic] Migrations completed successfully!", file=sys.stderr)
    except Exception as e:
        print(f"[Alembic ERROR] Failed to connect to database or run migrations: {e}", file=sys.stderr)
        print(
            f"[Alembic INFO] Database URL (first 50 chars): {database_url[:50]}...",
            file=sys.stderr,
        )
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
