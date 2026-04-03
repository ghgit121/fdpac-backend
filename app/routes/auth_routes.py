from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, rate_limit
from app.database import get_db
from app.schemas.auth_schema import LoginRequest, MeResponse, RegisterRequest
from app.services.auth_service import login_user, register_user
from app.utils.response import success_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db), _: None = Depends(rate_limit)):
    user = register_user(payload, db)
    return success_response(
        message="User registered successfully",
        data={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": "viewer",
            "is_active": user.is_active,
        },
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db), _: None = Depends(rate_limit)):
    token_data = login_user(payload, db)
    return success_response(message="Login successful", data=token_data)


@router.get("/me", response_model=MeResponse)
def me(current_user=Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.name,
        is_active=current_user.is_active,
    )
