from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# Append prepared_statement_cache_size to URL so SQLAlchemy's dialect uses it
db_url = settings.async_database_url
connect_args = {}

if "postgresql" in db_url.lower():
    if "prepared_statement_cache_size" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}prepared_statement_cache_size=0"
    connect_args["statement_cache_size"] = 0
elif "sqlite" in db_url.lower():
    connect_args["check_same_thread"] = False

from sqlalchemy import event

engine = create_async_engine(
    db_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Patch for SQLAlchemy 2.0.41 + asyncpg 0.30.0 incompatibility
@event.listens_for(engine.sync_engine, "do_connect")
def receive_do_connect(dialect, conn_rec, cargs, cparams):
    cparams.pop("channel_binding", None)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
# Backward-compatible alias used by some tests/helpers.
SessionLocal = AsyncSessionLocal


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
