from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import get_db
from app.auth.dependencies import require_admin
from app.services.notification_service import celery_app

# ??? ??? ???? ????? model_registry/app_settings:
from app.models.model_registry import ModelRegistry
from app.models.app_setting import AppSetting


router = APIRouter(prefix="/admin", tags=["admin"])


class SettingUpsert(BaseModel):
    value: Optional[str] = None
    is_secret: bool = False


@router.get("/settings/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    row = await db.execute(select(AppSetting).where(AppSetting.key == key))
    s = row.scalar_one_or_none()
    return {"key": key, "value": (s.value if s else None), "is_secret": bool(s.is_secret) if s else False}


@router.post("/settings/{key}")
async def set_setting(key: str, body: SettingUpsert, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    row = await db.execute(select(AppSetting).where(AppSetting.key == key))
    s = row.scalar_one_or_none()
    if s is None:
        s = AppSetting(key=key, value=body.value, is_secret=body.is_secret)
        db.add(s)
    else:
        s.value = body.value
        s.is_secret = body.is_secret

    await db.commit()
    return {"ok": True, "key": key}


@router.get("/models/active")
async def get_active_models(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin)
):
    q = select(ModelRegistry).where(ModelRegistry.is_active == True)
    if symbol:
        q = q.where(ModelRegistry.symbol == symbol)
    if timeframe:
        q = q.where(ModelRegistry.timeframe == timeframe)

    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "models": [
            {
                "model_type": r.model_type,
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "version": r.version,
                "artifact_path": r.artifact_path,
                "metrics": r.metrics,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


class TrainRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "M15"


@router.post("/train-models")
async def train_models_now(
    body: TrainRequest,
    _=Depends(require_admin)
):
    """
    ???? ????? ??????? ??? Celery (XGB/LGBM/LSTM ??? ????).
    ???? task_id ?????? ?? Celery backend.
    """
    # ??? ???ask ??? ?? ????? fully-qualified name
    task = celery_app.send_task(
        "app.ai.training.tasks.train_models",
        kwargs={"symbol": body.symbol, "timeframe": body.timeframe},
    )
    return {"queued": True, "task_id": task.id, "symbol": body.symbol, "timeframe": body.timeframe}