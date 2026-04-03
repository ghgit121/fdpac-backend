from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user_schema import UserCreateRequest, UserUpdateRequest


async def _get_role_by_name(db: AsyncSession, role_name: str) -> Role:
    role_result = await db.execute(select(Role).where(Role.name == role_name.lower()))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
    return role


async def create_user(payload: UserCreateRequest, db: AsyncSession) -> User:
    existing_result = await db.execute(select(User).where(User.email == payload.email))
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    role = await _get_role_by_name(db, payload.role_name)
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await get_user_or_404(user.id, db)


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).options(selectinload(User.role)).order_by(User.id.asc()))
    return list(result.scalars().all())


async def get_user_or_404(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def update_user(user_id: int, payload: UserUpdateRequest, db: AsyncSession) -> User:
    user = await get_user_or_404(user_id, db)

    if payload.email and payload.email != user.email:
        existing_result = await db.execute(select(User).where(User.email == payload.email))
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        user.email = payload.email

    if payload.name:
        user.name = payload.name
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.role_name:
        role = await _get_role_by_name(db, payload.role_name)
        user.role_id = role.id

    await db.commit()
    await db.refresh(user)
    return await get_user_or_404(user_id, db)


async def set_user_status(user_id: int, is_active: bool, db: AsyncSession) -> User:
    user = await get_user_or_404(user_id, db)
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    return await get_user_or_404(user_id, db)


async def delete_user(user_id: int, db: AsyncSession):
    user = await get_user_or_404(user_id, db)
    await db.delete(user)
    await db.commit()
