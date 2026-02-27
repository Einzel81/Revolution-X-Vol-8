from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
import random

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_trader
from app.database.connection import get_db
from app.models.candle import Candle

router = APIRouter()

_TF_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

@router.get("/historical")
async def historical(
    symbol: str = "XAUUSD",
    timeframe: str | None = None,
    tf: str | None = None,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_trader),
):
    # Frontend calls: /api/market-data/historical?symbol=XAUUSD&tf=1h&limit=200
    # We accept both `timeframe` and `tf`.
    raw_tf = (timeframe or tf or "M15").upper().strip()
    raw_tf = raw_tf.replace("1H", "H1").replace("4H", "H4")
    if raw_tf in {"60", "H"}:
        raw_tf = "H1"
    if raw_tf in {"15", "M"}:
        raw_tf = "M15"
    tf_norm = raw_tf

    # 1) Try DB first (real candles)
    try:
        q = (
            select(Candle)
            .where(Candle.symbol == symbol.upper())
            .where(Candle.timeframe == tf_norm)
            .order_by(desc(Candle.time))
            .limit(int(limit))
        )
        rows = (await db.execute(q)).scalars().all()
        if rows:
            rows = list(reversed(rows))
            return [
                {
                    "time": r.time.isoformat(),
                    "open": float(r.open),
                    "high": float(r.high),
                    "low": float(r.low),
                    "close": float(r.close),
                    "volume": float(r.volume) if r.volume is not None else None,
                }
                for r in rows
            ]
    except Exception:
        # Fall back to mock generation
        pass

    # 2) Mock fallback (until ingestion is enabled)
    tf = tf_norm
    step_min = _TF_MINUTES.get(tf, 15)

    now = datetime.utcnow().replace(second=0, microsecond=0)
    start = now - timedelta(minutes=step_min * limit)

    # Mock candles (?????? ?????? ??????? MT5/Provider)
    base = 1.0900 if symbol.upper() == "EURUSD" else 2945.0
    candles = []
    price = base

    for i in range(limit):
        t = start + timedelta(minutes=step_min * i)
        o = price + random.uniform(-0.002, 0.002) if base < 10 else price + random.uniform(-10, 10)
        c = o + (random.uniform(-0.0015, 0.0015) if base < 10 else random.uniform(-5, 5))
        h = max(o, c) + (random.uniform(0, 0.001) if base < 10 else random.uniform(0, 3))
        l = min(o, c) - (random.uniform(0, 0.001) if base < 10 else random.uniform(0, 3))
        v = random.randint(500, 5000)

        candles.append({
            "timestamp": int(t.timestamp() * 1000),  # ms ??? ??? ??? frontend ???? /1000
            "open": round(o, 5 if base < 10 else 2),
            "high": round(h, 5 if base < 10 else 2),
            "low": round(l, 5 if base < 10 else 2),
            "close": round(c, 5 if base < 10 else 2),
            "volume": v,
        })
        price = c

    return [
        {
            "time": c["timestamp"],
            "open": c["open"],
            "high": c["high"],
            "low": c["low"],
            "close": c["close"],
            "volume": c.get("volume"),
        }
        for c in candles
    ]