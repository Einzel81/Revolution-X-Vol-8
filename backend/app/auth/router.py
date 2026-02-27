# backend/app/auth/router.py

from __future__ import annotations

import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import security_manager
from app.database.connection import AsyncSessionLocal
from app.models.user import User

router = APIRouter()


# -----------------------------
# DB Dependency
# -----------------------------
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# -----------------------------
# Schemas
# -----------------------------
class UserPublic(BaseModel):
    """
    Fix: id must be UUID (not str) to avoid Pydantic v2 validation error.
    Also enable from_attributes so we can validate from ORM objects.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    two_factor_enabled: bool
    created_at: datetime.datetime | None = None
    last_login: datetime.datetime | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    two_factor_code: Optional[str] = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1)
    role: Optional[str] = None  # "admin"|"manager"|"trader"|"viewer" (optional)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


# -----------------------------
# Helpers
# -----------------------------
async def _get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    q = select(User).where(User.email == email)
    res = await db.execute(q)
    return res.scalar_one_or_none()


def _role_to_str(role_value) -> str:
    # Handles enum values, plain strings, etc.
    return getattr(role_value, "value", str(role_value))


def _user_to_public(user: User) -> UserPublic:
    # Build safe dict so role is always string; id is UUID (Pydantic accepts UUID).
    payload = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": _role_to_str(user.role),
        "is_active": bool(user.is_active),
        "two_factor_enabled": bool(user.two_factor_enabled),
        "created_at": user.created_at,
        "last_login": user.last_login,
    }
    return UserPublic.model_validate(payload)


# -----------------------------
# Routes
# -----------------------------
@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    email = data.email.strip().lower()
    password = data.password

    user = await _get_user_by_email(db, email)
    if not user or not security_manager.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # If your project actually enforces 2FA, wire it here.
    # For now we only block when enabled but no code provided.
    if getattr(user, "two_factor_enabled", False):
        if not data.two_factor_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA code required",
            )
        # TODO: validate two_factor_code against user.two_factor_secret

    # update last_login (non-blocking)
    user.last_login = datetime.datetime.utcnow()
    await db.commit()

    role_str = _role_to_str(user.role)

    # IMPORTANT: only put JSON-friendly primitives in JWT payload
    access_token = security_manager.create_access_token(
    subject=str(user.id),
    additional_claims={
        "email": user.email,
        "role": _role_to_str(user.role),
    },
)
    refresh_token = security_manager.create_refresh_token(subject=str(user.id))

    expires_seconds = int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)) * 60

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_seconds,
        user=_user_to_public(user),
    )


@router.post("/register", response_model=UserPublic, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserPublic:
    email = data.email.strip().lower()

    existing = await _get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = security_manager.hash_password(data.password)

    # Role: if provided, keep lowercase; otherwise default in model/db.
    role = (data.role or "").strip().lower() or None

    user = User(
        email=email,
        password_hash=password_hash,
        full_name=data.full_name.strip(),
        role=role if role else getattr(User, "role").default.arg if getattr(User, "role", None) and getattr(User.role, "default", None) else "trader",
        is_active=True,
        is_verified=False,
        two_factor_enabled=False,
    )
    db.add(user)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register user: {e}")

    await db.refresh(user)
    return _user_to_public(user)


@router.post("/refresh", response_model=dict)
async def refresh(data: RefreshRequest) -> dict:
    """
    Returns a new access_token (+ refresh_token if your security_manager rotates it).
    This assumes security_manager has decode/refresh helpers.
    If not, adjust to your actual implementation in app/core/security.py.
    """
    try:
        payload = security_manager.decode_token(data.refresh_token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access = security_manager.create_access_token(subject=str(sub), additional_claims={})
        # If you rotate refresh tokens, generate a new one; otherwise keep the same.
        new_refresh = security_manager.create_refresh_token(subject=str(sub))

        expires_seconds = int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)) * 60
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": expires_seconds,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout", response_model=dict)
async def logout(_: LogoutRequest) -> dict:
    # Stateless JWT: nothing to revoke unless you implement a blacklist.
    return {"ok": True}