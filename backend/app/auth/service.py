# backend/app/auth/service.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


# ? ???? ??????? ???? ?????? ????? ?????? ($2b$...)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    # -----------------------
    # Password
    # -----------------------
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    # -----------------------
    # JWT Tokens
    # -----------------------
    def create_access_token(self, subject: str, expires_minutes: Optional[int] = None) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=expires_minutes or getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        )
        to_encode = {"sub": subject, "exp": expire}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=getattr(settings, "ALGORITHM", "HS256"))

    # -----------------------
    # DB helpers
    # -----------------------
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        res = await db.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(db, email)
        if not user:
            return None
        if not user.is_active:
            return None
        # ? ?????? ?????? ?? DB
        if not self.verify_password(password, user.password_hash):
            return None
        return user


# ? instance ???? ??? ?? ??????? router
auth_service = AuthService()