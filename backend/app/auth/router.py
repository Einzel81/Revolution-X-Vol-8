# backend/app/auth/router.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.auth.models import UserRole
from app.auth.schemas import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, TokenResponse,
    PasswordChange, TwoFactorSetup, TwoFactorVerify, AuditLogResponse
)
from app.auth.service import AuthService
from app.auth.dependencies import (
    get_current_user, require_admin, require_manager, require_trader
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Public routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user (admin only can create users)"""
    auth_service = AuthService(db)
    try:
        user = await auth_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens"""
    auth_service = AuthService(db)
    try:
        # Get client IP
        ip = request.client.host if request.client else None
        return await auth_service.authenticate(login_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    auth_service = AuthService(db)
    try:
        return await auth_service.refresh_token(refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout(
    refresh_token: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke session"""
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id, refresh_token)
    return {"message": "Successfully logged out"}

# Protected routes
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    auth_service = AuthService(db)
    try:
        return await auth_service.update_user(current_user.id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(current_user.id)
    
    if not auth_service.verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    user.password_hash = auth_service.get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}

# 2FA routes
@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Setup 2FA for current user"""
    auth_service = AuthService(db)
    return await auth_service.setup_2fa(current_user.id)

@router.post("/2fa/verify")
async def verify_2fa(
    verify_data: TwoFactorVerify,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify and enable 2FA"""
    auth_service = AuthService(db)
    try:
        await auth_service.verify_and_enable_2fa(current_user.id, verify_data)
        return {"message": "2FA enabled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Admin routes
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponse = Depends(require_manager),
    db: AsyncSession = Depends(get_db)
):
    """List all users (manager and admin only)"""
    from sqlalchemy import select
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: UserResponse = Depends(require_manager),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update any user (admin only)"""
    auth_service = AuthService(db)
    try:
        return await auth_service.update_user(user_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    auth_service = AuthService(db)
    try:
        await auth_service.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Audit logs
@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user audit logs"""
    auth_service = AuthService(db)
    logs = await auth_service.get_user_audit_logs(current_user.id, limit)
    return logs

@router.get("/admin/audit-logs", response_model=List[AuditLogResponse])
async def get_all_audit_logs(
    limit: int = 1000,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all audit logs (admin only)"""
    from sqlalchemy import select
    from app.auth.models import AuditLog
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
