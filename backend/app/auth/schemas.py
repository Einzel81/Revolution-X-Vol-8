# backend/app/auth/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.auth.models import UserRole

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.TRADER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    created_by: Optional[UUID] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    password_hash: str

# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    two_factor_code: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenPayload(BaseModel):
    sub: UUID  # user_id
    exp: datetime
    type: str  # access or refresh
    role: UserRole

# Password schemas
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

# 2FA schemas
class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: str

class TwoFactorVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

# Audit log schemas
class AuditLogCreate(BaseModel):
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
