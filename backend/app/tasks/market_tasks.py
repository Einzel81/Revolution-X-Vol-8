from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import AsyncSessionLocal
from app.models.candle import Candle
from app.mt5.connector import mt5_connector
from app.services.activity_bus import activity_bus


def _to_dt(ts: Any) -> datetime:
    if isinstance(ts, (int, float)):
        return datetime.utcfromtimestamp(ts)
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


async def _insert_new_candles(db: AsyncSession, symbol: str, timeframe: str, rates: List[Dict[str, Any]]) -> int:
    inserted = 0
    for r in rates:
        t = _to_dt(r.get("time") or r.get("timestamp"))
        exists_q = select(Candle.id).where(
            (Candle.symbol == symbol) & (Candle.timeframe == timeframe) & (Candle.time == t)
        )
        exists = (await db.execute(exists_q)).scalar_one_or_none()
        if exists:
            continue

        db.add(
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                time=t,
                open=float(r.get("open")),
                high=float(r.get("high")),
                low=float(r.get("low")),
                close=float(r.get("close")),
                volume=float(r.get("tick_volume") or r.get("volume") or 0),
            )
        )
        inserted += 1

    await db.commit()
    return inserted


@shared_task(name="app.tasks.market_tasks.ingest_and_scan")
def ingest_and_scan(symbol: str = "XAUUSD", timeframe: str = "M15", count: int = 200) -> str:
    rates: Optional[List[Dict[str, Any]]] = None

    try:
        rates = mt5_connector.get_rates(symbol=symbol, timeframe=timeframe, count=count)
    except TypeError:
        async def _get():
            return await mt5_connector.get_rates(symbol=symbol, timeframe=timeframe, count=count)
        rates = asyncio.run(_get())

    if not rates:
        return "no_data"

    async def _run():
        async with AsyncSessionLocal() as db:
            inserted = await _insert_new_candles(db, symbol, timeframe, rates)

        await activity_bus.publish(
            {
                "event": "candles_ingested",
                "symbol": symbol,
                "timeframe": timeframe,
                "inserted": inserted,
            }
        )

    asyncio.run(_run())
    return "ok"
