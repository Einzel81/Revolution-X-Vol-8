from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
import random

from app.auth.dependencies import require_trader

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
    symbol: str = "EURUSD",
    timeframe: str = "M15",
    limit: int = 200,
    current_user=Depends(require_trader),
):
    tf = timeframe.upper()
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

    return {
        "symbol": symbol,
        "timeframe": tf,
        "candles": candles,
        "orderBlocks": [],
        "tradeMarkers": [],
    }