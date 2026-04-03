import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

TEST_DB_PATH = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.role import Role


async def _seed_roles():
    async with SessionLocal() as session:
        for name, description in [
            ("viewer", "Can only view dashboard data"),
            ("analyst", "Can view records and dashboard insights"),
            ("admin", "Can create update delete records and manage users"),
        ]:
            exists_result = await session.execute(select(Role).where(Role.name == name))
            exists = exists_result.scalar_one_or_none()
            if not exists:
                session.add(Role(name=name, description=description))
        await session.commit()


async def _reset_schema():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def _drop_schema():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    _run(_reset_schema())
    _run(_seed_roles())
    yield
    _run(_drop_schema())


@pytest.fixture(autouse=True)
def clean_tables():
    async def _clean():
        async with SessionLocal() as session:
            await session.execute(text("DELETE FROM financial_records"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()

    _run(_clean())


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def create_user(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code in (200, 201)
    return response.json()


def login_user(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]
