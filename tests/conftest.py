import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

TEST_DB_PATH = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.role import Role


def _seed_roles():
    session = SessionLocal()
    try:
        for name, description in [
            ("viewer", "Can only view dashboard data"),
            ("analyst", "Can view records and dashboard insights"),
            ("admin", "Can create update delete records and manage users"),
        ]:
            exists = session.query(Role).filter(Role.name == name).first()
            if not exists:
                session.add(Role(name=name, description=description))
        session.commit()
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _seed_roles()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    session = SessionLocal()
    try:
        session.execute(text("DELETE FROM financial_records"))
        session.execute(text("DELETE FROM users"))
        session.commit()
    finally:
        session.close()


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
