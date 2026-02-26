from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database.connection import get_db
from app.auth.dependencies import require_trader
from app.mt5.connector import mt5_connector
from app.models.execution_event import ExecutionEvent


router = APIRouter()


@router.get("/health")
async def execution_health(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    """Execution bridge health + last-hour metrics."""

    ping = await mt5_connector.ping(timeout_ms=800)

    since = datetime.utcnow() - timedelta(hours=1)
    q = select(func.count(ExecutionEvent.id)).where(ExecutionEvent.created_at >= since)
    total = int((await db.execute(q)).scalar_one() or 0)

    q_ok = select(func.count(ExecutionEvent.id)).where(
        (ExecutionEvent.created_at >= since) & (ExecutionEvent.status == "success")
    )
    ok = int((await db.execute(q_ok)).scalar_one() or 0)

    q_err = select(func.count(ExecutionEvent.id)).where(
        (ExecutionEvent.created_at >= since) & (ExecutionEvent.status.in_(["error", "blocked"]))
    )
    bad = int((await db.execute(q_err)).scalar_one() or 0)

    return {
        "bridge": {
            "connected": bool(getattr(mt5_connector, "connected", False)),
            "ping": ping,
        },
        "last_hour": {
            "total": total,
            "success": ok,
            "bad": bad,
            "success_rate": (ok / total) if total else None,
        },
    }


@router.get("/events")
async def execution_events(limit: int = 50, db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    limit = max(1, min(500, int(limit)))
    q = select(ExecutionEvent).order_by(desc(ExecutionEvent.created_at)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "user_id": r.user_id,
                "source": r.source,
                "symbol": r.symbol,
                "side": r.side,
                "volume": r.volume,
                "requested_price": r.requested_price,
                "fill_price": r.fill_price,
                "slippage": r.slippage,
                "latency_ms": r.latency_ms,
                "status": r.status,
                "ticket": r.ticket,
                "error": r.error,
            }
            for r in rows
        ],
    }