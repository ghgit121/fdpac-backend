from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.role import Role
from app.models.user import User


def test_register_and_login_success(client):
    register = client.post(
        "/api/v1/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert register.status_code == 201

    login = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"})
    assert login.status_code == 200
    assert login.json()["data"]["access_token"]


def test_invalid_login(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )
    bad = client.post("/api/v1/auth/login", json={"email": "bob@example.com", "password": "wrongpass123"})
    assert bad.status_code == 401


def test_expired_token(client):
    session = SessionLocal()
    role = session.query(Role).filter(Role.name == "viewer").first()
    user = User(
        name="Expired User",
        email="expired@example.com",
        password_hash=hash_password("password123"),
        role_id=role.id,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()

    payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    expired = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
