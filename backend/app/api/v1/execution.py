from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database.connection import get_db
from app.auth.dependencies import require_trader
from app.mt5.connector import mt5_connector
from app.models.execution_event import ExecutionEvent
from app.models.mt5_position_snapshot import MT5PositionSnapshot
from app.services.settings_service import SettingsService

router = APIRouter()


async def _apply_runtime_settings(db: AsyncSession) -> None:
    svc = SettingsService(db)
    host = await svc.get("MT5_HOST")
    port = await svc.get("MT5_PORT")
    if host:
        mt5_connector.set_endpoint(host, int(port or 9000))


@router.get("/health")
async def execution_health(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    await _apply_runtime_settings(db)
    ping = await mt5_connector.ping(timeout_ms=800)

    since = datetime.utcnow() - timedelta(hours=1)
    q_total = select(func.count(ExecutionEvent.id)).where(ExecutionEvent.created_at >= since)
    total = int((await db.execute(q_total)).scalar_one() or 0)

    q_ok = select(func.count(ExecutionEvent.id)).where(
        (ExecutionEvent.created_at >= since) & (ExecutionEvent.status == "success")
    )
    ok = int((await db.execute(q_ok)).scalar_one() or 0)

    q_bad = select(func.count(ExecutionEvent.id)).where(
        (ExecutionEvent.created_at >= since) & (ExecutionEvent.status.in_(["bad", "blocked", "error"]))
    )
    bad = int((await db.execute(q_bad)).scalar_one() or 0)

    return {
        "bridge": {"connected": bool(getattr(mt5_connector, "connected", False)), "ping": ping},
        "last_hour": {"total": total, "success": ok, "bad": bad, "success_rate": (ok / total) if total else None},
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


@router.get("/positions")
async def mt5_positions_live(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    await _apply_runtime_settings(db)
    resp = await mt5_connector.get_positions(timeout_ms=2500)
    ok = not (isinstance(resp, dict) and resp.get("error"))
    return {"ok": ok, "response": resp}


@router.post("/sync")
async def mt5_sync_positions(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    await _apply_runtime_settings(db)
    resp = await mt5_connector.get_positions(timeout_ms=2500)

    if isinstance(resp, dict) and resp.get("error"):
        return {"ok": False, "error": resp.get("error"), "response": resp}

    account_id = None
    items = None

    if isinstance(resp, dict):
        account_id = str((resp.get("account") or {}).get("login") or (resp.get("account") or {}).get("id") or "") or None
        items = resp.get("positions") or resp.get("items")
    else:
        items = resp

    if not isinstance(items, list):
        items = []

    upserted = 0
    for p in items:
        if not isinstance(p, dict):
            continue
        ticket = p.get("ticket") or p.get("id") or p.get("position")
        if ticket is None:
            continue
        ticket_s = str(ticket)

        symbol = str(p.get("symbol") or p.get("_symbol") or "")
        side_raw = str(p.get("type") or p.get("side") or p.get("action") or "").upper()
        if side_raw in ("0", "BUY", "LONG"):
            side = "BUY"
        elif side_raw in ("1", "SELL", "SHORT"):
            side = "SELL"
        else:
            side = side_raw or "UNKNOWN"

        volume = float(p.get("volume") or p.get("lots") or 0.0)
        open_price = p.get("price_open") or p.get("open_price") or p.get("price")
        sl = p.get("sl")
        tp = p.get("tp")
        profit = p.get("profit")
        swap = p.get("swap")
        commission = p.get("commission")
        magic = p.get("magic")
        comment = p.get("comment")

        open_time = None
        t = p.get("time") or p.get("time_open") or p.get("open_time")
        if isinstance(t, (int, float)):
            try:
                open_time = datetime.utcfromtimestamp(int(t))
            except Exception:
                open_time = None

        q = select(MT5PositionSnapshot).where(
            (MT5PositionSnapshot.ticket == ticket_s) & (MT5PositionSnapshot.account_id == account_id)
        )
        existing = (await db.execute(q)).scalar_one_or_none()

        if not existing:
            existing = MT5PositionSnapshot(account_id=account_id, ticket=ticket_s)
            db.add(existing)

        existing.symbol = symbol or existing.symbol
        existing.side = side or existing.side
        existing.volume = float(volume)
        existing.open_price = float(open_price) if open_price is not None else None
        existing.sl = float(sl) if sl is not None else None
        existing.tp = float(tp) if tp is not None else None
        existing.profit = float(profit) if profit is not None else None
        existing.swap = float(swap) if swap is not None else None
        existing.commission = float(commission) if commission is not None else None
        existing.open_time = open_time
        existing.magic = str(magic) if magic is not None else None
        existing.comment = str(comment) if comment is not None else None
        existing.raw = p

        upserted += 1

    await db.commit()
    return {"ok": True, "upserted": upserted, "account_id": account_id}


@router.get("/positions/snapshots")
async def mt5_positions_snapshots(limit: int = 200, db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    limit = max(1, min(1000, int(limit)))
    q = select(MT5PositionSnapshot).order_by(desc(MT5PositionSnapshot.updated_at)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "account_id": r.account_id,
                "ticket": r.ticket,
                "symbol": r.symbol,
                "side": r.side,
                "volume": r.volume,
                "open_price": r.open_price,
                "sl": r.sl,
                "tp": r.tp,
                "profit": r.profit,
                "swap": r.swap,
                "commission": r.commission,
                "open_time": r.open_time.isoformat() if r.open_time else None,
                "magic": r.magic,
                "comment": r.comment,
            }
            for r in rows
        ],
    }