from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import create_access_token, hash_password, verify_password
from app.models.role import Role
from app.models.user import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest


async def register_user(payload: RegisterRequest, db: AsyncSession) -> User:
    existing_result = await db.execute(select(User).where(User.email == payload.email))
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    role_result = await db.execute(select(Role).where(Role.name == "viewer"))
    viewer_role = role_result.scalar_one_or_none()
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
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(payload: LoginRequest, db: AsyncSession) -> dict:
    user_result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.email == payload.email)
    )
    user = user_result.scalar_one_or_none()
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
