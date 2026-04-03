from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user_schema import UserCreateRequest, UserUpdateRequest


def _get_role_by_name(db: Session, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name.lower()).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
    return role


def create_user(payload: UserCreateRequest, db: Session) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    role = _get_role_by_name(db, payload.role_name)
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).options(joinedload(User.role)).order_by(User.id.asc()).all()


def get_user_or_404(user_id: int, db: Session) -> User:
    user = db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def update_user(user_id: int, payload: UserUpdateRequest, db: Session) -> User:
    user = get_user_or_404(user_id, db)

    if payload.email and payload.email != user.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        user.email = payload.email

    if payload.name:
        user.name = payload.name
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.role_name:
        role = _get_role_by_name(db, payload.role_name)
        user.role_id = role.id

    db.commit()
    db.refresh(user)
    return get_user_or_404(user_id, db)


def set_user_status(user_id: int, is_active: bool, db: Session) -> User:
    user = get_user_or_404(user_id, db)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def delete_user(user_id: int, db: Session):
    user = get_user_or_404(user_id, db)
    db.delete(user)
    db.commit()
