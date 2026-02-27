from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from celery import shared_task
from sqlalchemy import select

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


async def _maybe_await(x: Any) -> Any:
    if hasattr(x, "__await__"):
        return await x
    return x


async def _get_rates_safe(symbol: str, timeframe: str, count: int) -> List[Dict[str, Any]]:
    """
    ????: get_rates sync ?? async? ????? ?????? List.
    """
    res = mt5_connector.get_rates(symbol=symbol, timeframe=timeframe, count=count)
    res = await _maybe_await(res)

    # ??????? ??? connectors ?????? coroutine ???? coroutine
    while hasattr(res, "__await__"):
        res = await res

    if res is None:
        return []
    if isinstance(res, list):
        return res
    # ?? ??? dict ??? rates
    if isinstance(res, dict):
        for k in ("rates", "data", "candles"):
            v = res.get(k)
            if isinstance(v, list):
                return v
    return []


async def _insert_new_candles(db, symbol: str, timeframe: str, rates: List[Dict[str, Any]]) -> int:
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
    async def _run() -> str:
        rates = await _get_rates_safe(symbol=symbol, timeframe=timeframe, count=count)
        if not rates:
            return "no_data"

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
        return "ok"

    return asyncio.run(_run())