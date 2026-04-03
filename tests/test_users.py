import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.role import Role
from app.models.user import User


def _run(coro):
    return asyncio.run(coro)


def _create_admin():
    async def _create():
        async with SessionLocal() as session:
            role_result = await session.execute(select(Role).where(Role.name == "admin"))
            role = role_result.scalar_one()
            user = User(
                name="Admin",
                email="admin@example.com",
                password_hash=hash_password("password123"),
                role_id=role.id,
                is_active=True,
            )
            session.add(user)
            await session.commit()

    _run(_create())


def _create_viewer():
    async def _create():
        async with SessionLocal() as session:
            role_result = await session.execute(select(Role).where(Role.name == "viewer"))
            role = role_result.scalar_one()
            user = User(
                name="Viewer",
                email="viewer@example.com",
                password_hash=hash_password("password123"),
                role_id=role.id,
                is_active=True,
            )
            session.add(user)
            await session.commit()

    _run(_create())


def _login(client, email: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return response.json()["data"]["access_token"]


def test_admin_can_create_and_disable_user(client):
    _create_admin()
    token = _login(client, "admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/users",
        json={
            "name": "Analyst User",
            "email": "analyst@example.com",
            "password": "password123",
            "role_name": "analyst",
        },
        headers=headers,
    )
    assert create.status_code == 201
    user_id = create.json()["data"]["id"]

    disable = client.patch(f"/api/v1/users/{user_id}/status", json={"is_active": False}, headers=headers)
    assert disable.status_code == 200
    assert disable.json()["data"]["is_active"] is False


def test_viewer_cannot_create_user(client):
    _create_viewer()
    token = _login(client, "viewer@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/users",
        json={
            "name": "Other",
            "email": "other@example.com",
            "password": "password123",
            "role_name": "viewer",
        },
        headers=headers,
    )
    assert create.status_code == 403
