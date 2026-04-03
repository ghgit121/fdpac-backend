from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.role_checker import require_roles
from app.database import get_db
from app.schemas.user_schema import UserCreateRequest, UserStatusPatchRequest, UserUpdateRequest
from app.services import user_service
from app.utils.response import success_response

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", dependencies=[Depends(require_roles("admin"))])
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    user = user_service.create_user(payload, db)
    return success_response(
        "User created successfully",
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.name,
            "is_active": user.is_active,
        },
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", dependencies=[Depends(require_roles("admin"))])
def list_users(db: Session = Depends(get_db)):
    users = user_service.list_users(db)
    return success_response(
        "Users fetched successfully",
        [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role.name,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
    )


@router.get("/{user_id}", dependencies=[Depends(require_roles("admin"))])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.get_user_or_404(user_id, db)
    return success_response(
        "User fetched successfully",
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        },
    )


@router.put("/{user_id}", dependencies=[Depends(require_roles("admin"))])
def update_user(user_id: int, payload: UserUpdateRequest, db: Session = Depends(get_db)):
    user = user_service.update_user(user_id, payload, db)
    return success_response(
        "User updated successfully",
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        },
    )


@router.patch("/{user_id}/status", dependencies=[Depends(require_roles("admin"))])
def patch_user_status(user_id: int, payload: UserStatusPatchRequest, db: Session = Depends(get_db)):
    user = user_service.set_user_status(user_id, payload.is_active, db)
    return success_response(
        "User status updated successfully",
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        },
    )


@router.delete("/{user_id}", dependencies=[Depends(require_roles("admin"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user_service.delete_user(user_id, db)
    return success_response("User deleted successfully", None)
