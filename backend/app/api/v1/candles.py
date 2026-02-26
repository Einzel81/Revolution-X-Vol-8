from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database.connection import get_db
from app.auth.dependencies import require_trader, require_admin
from app.models.candle import Candle

router = APIRouter()

class CandleIn(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

class IngestRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "M15"
    candles: List[CandleIn] = Field(..., min_items=1)

@router.post("/ingest")
async def ingest_candles(req: IngestRequest, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    """
    Ingestion endpoint: call it from MT5 bridge / data feeder.
    Uses UPSERT-like behavior by deleting duplicates on same PK.
    """
    # naive upsert: delete existing keys then insert
    for c in req.candles:
        await db.execute(
            Candle.__table__.delete().where(
                (Candle.time == c.time) &
                (Candle.symbol == req.symbol) &
                (Candle.timeframe == req.timeframe)
            )
        )
        db.add(Candle(
            time=c.time,
            symbol=req.symbol,
            timeframe=req.timeframe,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume
        ))

    await db.commit()
    return {"ok": True, "inserted": len(req.candles)}

@router.get("/latest")
async def get_latest(symbol: str, timeframe: str, limit: int = 300, db: AsyncSession = Depends(get_db), _=Depends(require_trader)):
    q = (
        select(Candle)
        .where((Candle.symbol == symbol) & (Candle.timeframe == timeframe))
        .order_by(desc(Candle.time))
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    rows = list(reversed(rows))
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(rows),
        "candles": [
            {"time": r.time, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume}
            for r in rows
        ]
    }