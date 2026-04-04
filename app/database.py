from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# Append required asyncpg query parameters to disable prepared statement caching for PgBouncer
db_url = settings.async_database_url
if "prepared_statement_cache_size" not in db_url:
    separator = "&" if "?" in db_url else "?"
    db_url += f"{separator}prepared_statement_cache_size=0&statement_cache_size=0"

engine = create_async_engine(
    db_url,
    pool_pre_ping=True,
)
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
