from app.core.security import hash_password
from app.database import SessionLocal
from app.models.role import Role
from app.models.user import User


def _create_user(email: str, role_name: str):
    session = SessionLocal()
    try:
        role = session.query(Role).filter(Role.name == role_name).first()
        user = User(
            name=role_name.title(),
            email=email,
            password_hash=hash_password("password123"),
            role_id=role.id,
            is_active=True,
        )
        session.add(user)
        session.commit()
    finally:
        session.close()


def _login(client, email: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_admin_creates_record(client):
    _create_user("admin@example.com", "admin")
    token = _login(client, "admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/records",
        headers=headers,
        json={"amount": 100.0, "type": "income", "category": "salary", "date": "2025-01-10", "notes": "jan"},
    )
    assert response.status_code == 201


def test_analyst_reads_records(client):
    _create_user("admin@example.com", "admin")
    _create_user("analyst@example.com", "analyst")

    admin_token = _login(client, "admin@example.com")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        "/api/v1/records",
        headers=admin_headers,
        json={"amount": 70.0, "type": "expense", "category": "food", "date": "2025-01-12", "notes": "meal"},
    )

    analyst_token = _login(client, "analyst@example.com")
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    read = client.get("/api/v1/records", headers=analyst_headers)
    assert read.status_code == 200
    assert len(read.json()["data"]["items"]) == 1


def test_viewer_cannot_create_record(client):
    _create_user("viewer@example.com", "viewer")
    viewer_token = _login(client, "viewer@example.com")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    create = client.post(
        "/api/v1/records",
        headers=viewer_headers,
        json={"amount": 10.0, "type": "expense", "category": "snacks", "date": "2025-01-15", "notes": "chips"},
    )
    assert create.status_code == 403


def test_invalid_amount_validation(client):
    _create_user("admin@example.com", "admin")
    token = _login(client, "admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/records",
        headers=headers,
        json={"amount": -5, "type": "expense", "category": "invalid", "date": "2025-01-10"},
    )
    assert response.status_code == 400
