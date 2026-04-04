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
            print("[Alembic] Direct connection established successfully.", file=sys.stderr)
            
            context.configure(
                connection=connection, 
                target_metadata=target_metadata,
                # Ensure we handle Neon DB's transaction pooler issues if accidentally used
                execution_options={"isolation_level": "AUTOCOMMIT"}
            )

            with context.begin_transaction():
                context.run_migrations()
            print("[Alembic] Migrations completed and transaction committed.", file=sys.stderr)
    except Exception as e:
        print(f"[Alembic CRITICAL] Execution failed: {e}", file=sys.stderr)
        if "relation" in str(e) and "already exists" in str(e):
            print("[HINT] Database schema might be partially migrated. Check MIGRATION_DATABASE_URL.", file=sys.stderr)
        elif "connection" in str(e).lower():
            print("[HINT] Verify MIGRATION_DATABASE_URL is a 'Direct Connection' string, not a pooler.", file=sys.stderr)
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
