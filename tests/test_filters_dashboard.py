from app.core.security import hash_password
from app.database import SessionLocal
from app.models.role import Role
from app.models.user import User


def _create_admin():
    session = SessionLocal()
    try:
        role = session.query(Role).filter(Role.name == "admin").first()
        user = User(
            name="Admin",
            email="admin@example.com",
            password_hash=hash_password("password123"),
            role_id=role.id,
            is_active=True,
        )
        session.add(user)
        session.commit()
    finally:
        session.close()


def _login(client):
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "password123"})
    return response.json()["data"]["access_token"]


def _create_seed_records(client, headers):
    payloads = [
        {"amount": 1000, "type": "income", "category": "salary", "date": "2025-01-01", "notes": "monthly salary"},
        {"amount": 200, "type": "expense", "category": "food", "date": "2025-01-02", "notes": "groceries"},
        {"amount": 500, "type": "income", "category": "freelance", "date": "2025-02-01", "notes": "project"},
        {"amount": 100, "type": "expense", "category": "food", "date": "2025-02-02", "notes": "dinner"},
    ]
    for payload in payloads:
        response = client.post("/api/v1/records", json=payload, headers=headers)
        assert response.status_code == 201


def test_filter_by_category_type_date_and_notes(client):
    _create_admin()
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _create_seed_records(client, headers)

    category = client.get("/api/v1/records?category=food", headers=headers)
    assert category.status_code == 200
    assert len(category.json()["data"]["items"]) == 2

    by_type = client.get("/api/v1/records?type=income", headers=headers)
    assert by_type.status_code == 200
    assert len(by_type.json()["data"]["items"]) == 2

    by_date = client.get("/api/v1/records?start_date=2025-02-01&end_date=2025-02-28", headers=headers)
    assert by_date.status_code == 200
    assert len(by_date.json()["data"]["items"]) == 2

    by_notes = client.get("/api/v1/records?notes=salary", headers=headers)
    assert by_notes.status_code == 200
    assert len(by_notes.json()["data"]["items"]) == 1


def test_dashboard_calculations(client):
    _create_admin()
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    _create_seed_records(client, headers)

    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    data = summary.json()["data"]
    assert data["total_income"] == 1500
    assert data["total_expense"] == 300
    assert data["net_balance"] == 1200

    monthly = client.get("/api/v1/dashboard/monthly-trends", headers=headers)
    assert monthly.status_code == 200
    assert len(monthly.json()["data"]) == 2

    categories = client.get("/api/v1/dashboard/category-breakdown", headers=headers)
    assert categories.status_code == 200
    assert len(categories.json()["data"]) >= 2
