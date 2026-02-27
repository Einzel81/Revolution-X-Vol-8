# backend/app/auth/dependencies.py
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.config import settings
from app.models.user import User

security = HTTPBearer(auto_error=False)
COOKIE_TOKEN_NAME = "revolution_x_token"


def _extract_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    # 1) Authorization header
    if credentials and credentials.credentials:
        return credentials.credentials

    # 2) Cookie
    cookie_token = request.cookies.get(COOKIE_TOKEN_NAME)
    if cookie_token:
        return cookie_token

    return None


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[getattr(settings, "ALGORITHM", "HS256")],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def _get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(token)

    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    try:
        user_id = UUID(sub)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from e

    user = await _get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    request.state.user = user
    return user


def require_role(*roles: str):
    async def _role_dep(user: User = Depends(get_current_user)) -> User:
        # ?? ???? user ???? ?????? role = "admin"|"trader"|...
        user_role = getattr(user, "role", None)
        if roles and user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        return user

    return _role_dep


# helpers ?????
require_admin = require_role("admin")
require_trader = require_role("admin", "trader")
require_manager = require_role("admin", "manager")