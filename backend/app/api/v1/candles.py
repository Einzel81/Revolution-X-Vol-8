from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_trader
from app.database.connection import get_db
from app.models.candle import Candle
from app.mt5.connector import mt5_connector
from app.services.settings_service import SettingsService


router = APIRouter()


def _norm_time(x: Any) -> datetime | None:
    """Accept epoch seconds/ms or ISO strings."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        # Heuristic: ms if > 10^11
        ts = float(x)
        if ts > 1e11:
            ts = ts / 1000.0
        return datetime.utcfromtimestamp(ts)
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        # If numeric string
        try:
            return _norm_time(float(s))
        except Exception:
            pass
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None
    return None


@router.get("/mt5")
async def get_mt5_rates(
    symbol: str = "XAUUSD",
    timeframe: str = "M15",
    count: int = 300,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_trader),
):
    """Fetch rates directly from MT5 bridge (no persistence)."""
    svc = SettingsService(db)
    host = await svc.get("MT5_HOST")
    port = await svc.get("MT5_PORT")
    if host:
        mt5_connector.set_endpoint(host, int(port or 9000))

    resp = await mt5_connector.get_rates(symbol=symbol, timeframe=timeframe, count=count, timeout_ms=3500)
    if isinstance(resp, dict) and resp.get("error"):
        raise HTTPException(status_code=502, detail=f"MT5 bridge error: {resp.get('error')}")

    items = resp.get("rates") if isinstance(resp, dict) else resp
    if not isinstance(items, list):
        items = resp.get("items") if isinstance(resp, dict) else []
    if not isinstance(items, list):
        items = []

    out: List[Dict[str, Any]] = []
    for x in items:
        if not isinstance(x, dict):
            continue
        t = x.get("time") or x.get("timestamp")
        out.append(
            {
                "time": t,
                "open": x.get("open"),
                "high": x.get("high"),
                "low": x.get("low"),
                "close": x.get("close"),
                "volume": x.get("tick_volume") or x.get("volume"),
            }
        )

    return {"symbol": symbol, "timeframe": timeframe, "count": len(out), "candles": out, "source": "mt5"}


@router.post("/ingest/mt5")
async def ingest_mt5_rates(
    symbol: str = "XAUUSD",
    timeframe: str = "M15",
    count: int = 300,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_trader),
):
    """Fetch rates from MT5 bridge and UPSERT into TimescaleDB candles table."""
    svc = SettingsService(db)
    host = await svc.get("MT5_HOST")
    port = await svc.get("MT5_PORT")
    if host:
        mt5_connector.set_endpoint(host, int(port or 9000))

    resp = await mt5_connector.get_rates(symbol=symbol, timeframe=timeframe, count=count, timeout_ms=4500)
    if isinstance(resp, dict) and resp.get("error"):
        raise HTTPException(status_code=502, detail=f"MT5 bridge error: {resp.get('error')}")

    items = resp.get("rates") if isinstance(resp, dict) else resp
    if not isinstance(items, list):
        items = resp.get("items") if isinstance(resp, dict) else []
    if not isinstance(items, list):
        items = []

    rows = []
    for x in items:
        if not isinstance(x, dict):
            continue
        t = _norm_time(x.get("time") or x.get("timestamp"))
        if not t:
            continue
        rows.append(
            {
                "time": t,
                "symbol": symbol.upper(),
                "timeframe": timeframe.upper(),
                "open": float(x.get("open")),
                "high": float(x.get("high")),
                "low": float(x.get("low")),
                "close": float(x.get("close")),
                "volume": float(x.get("tick_volume") or x.get("volume") or 0.0),
                "epoch_ms": int(float(x.get("time") or x.get("timestamp") or 0) * (1000 if float(x.get("time") or x.get("timestamp") or 0) < 1e11 else 1)),
            }
        )

    if not rows:
        return {"status": "ok", "inserted": 0}

    stmt = insert(Candle).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Candle.time, Candle.symbol, Candle.timeframe],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
            "epoch_ms": stmt.excluded.epoch_ms,
        },
    )
    await db.execute(stmt)
    await db.commit()

    return {"status": "ok", "upserted": len(rows), "symbol": symbol, "timeframe": timeframe}
