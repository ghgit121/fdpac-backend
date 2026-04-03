from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import create_access_token, hash_password, verify_password
from app.models.role import Role
from app.models.user import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest


def register_user(payload: RegisterRequest, db: Session) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    viewer_role = db.query(Role).filter(Role.name == "viewer").first()
    if not viewer_role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default role missing")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=viewer_role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(payload: LoginRequest, db: Session) -> dict:
    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.email == payload.email)
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")

    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 24 * 60,
    }
