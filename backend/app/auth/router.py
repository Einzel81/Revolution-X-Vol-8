# backend/app/auth/router.py

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.user import User
from app.core.security import security_manager

# Compatibility enum (we fixed it in app/auth/models.py)
from app.auth.models import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


# -----------------------------
# Schemas (self-contained)
# -----------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: Optional[UserRole] = None  # default set in code


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class LoginResponse(TokenResponse):
    user: UserPublic


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


# -----------------------------
# Helpers
# -----------------------------
async def _get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    q = select(User).where(User.email == email)
    res = await db.execute(q)
    return res.scalar_one_or_none()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


# -----------------------------
# Routes
# -----------------------------
@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = _normalize_email(str(data.email))
    password = data.password

    user = await _get_user_by_email(db, email)
    if not user:
        # ??? ??????? ?????? ?????
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Gatekeeping ????
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    if user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not verified",
        )

    # Verify password against users.password_hash
    if not security_manager.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Tokens
    access_token = security_manager.create_access_token(
        subject=str(user.id),
        additional_claims={"role": str(user.role), "email": user.email},
    )
    refresh_token = None
    # ??? ???? REFRESH_TOKEN_EXPIRE_DAYS ?? settings (????? ?? security_manager)? ???? ?????
    try:
        refresh_token = security_manager.create_refresh_token(subject=str(user.id))
    except Exception:
        refresh_token = None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user": user,
    }


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = _normalize_email(str(data.email))

    existing = await _get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Default role = VIEWER (safe)
    role = data.role or UserRole.VIEWER

    password_hash = security_manager.hash_password(data.password)

    # Important: your DB user.id is UUID. Most projects define default in model.
    # If your model DOES NOT define default, add uuid here. We'll try safe fallback.
    try:
        import uuid

        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            full_name=data.full_name,
            role=role.value if hasattr(role, "value") else str(role),
            is_active=True,
            is_verified=True,  # ????? ????? False ??? ???? flow ???? verification
            two_factor_enabled=False,
            metadata={},
        )
    except Exception:
        # If the model already generates id/defaults, this works
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=data.full_name,
            role=role.value if hasattr(role, "value") else str(role),
            is_active=True,
            is_verified=True,
            two_factor_enabled=False,
            metadata={},
        )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    # ??? ???? dependency get_current_user? ???? ?????? ???.
):
    # ???? get_current_user ?? ????? ???? ???? ???????? ??????
    raise HTTPException(
        status_code=501,
        detail="change-password requires get_current_user dependency wiring",
    )