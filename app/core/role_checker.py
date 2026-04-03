from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import User


def require_roles(*allowed_roles: str):
    allowed = {role.lower() for role in allowed_roles}

    async def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.name.lower() if current_user.role else ""
        if role_name not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for this role")
        return current_user

    return role_dependency
