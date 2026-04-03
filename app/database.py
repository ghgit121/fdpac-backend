from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.async_database_url, pool_pre_ping=True)
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
