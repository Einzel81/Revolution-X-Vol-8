from __future__ import annotations

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.auth.dependencies import require_admin
from app.services.settings_service import SettingsService


router = APIRouter()


class SettingUpsert(BaseModel):
    key: str = Field(..., min_length=2, max_length=128)
    value: Optional[str] = None
    is_secret: bool = False


@router.get("/settings")
async def list_settings(db: AsyncSession = Depends(get_db), _=Depends(require_admin)) -> Dict[str, Any]:
    svc = SettingsService(db)
    return await svc.get_public_settings()


@router.put("/settings")
async def upsert_setting(payload: SettingUpsert, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    svc = SettingsService(db)
    await svc.set(payload.key, payload.value, is_secret=payload.is_secret)
    return {"ok": True, "key": payload.key}