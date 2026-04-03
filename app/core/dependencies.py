import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_request_log: dict[str, list[datetime]] = {}
_rate_lock = asyncio.Lock()


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return user


async def rate_limit(request: Request):
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.url.path}"
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=1)

    async with _rate_lock:
        history = _request_log.get(key, [])
        history = [ts for ts in history if ts >= window_start]
        if len(history) >= settings.rate_limit_per_minute:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        history.append(now)
        _request_log[key] = history
