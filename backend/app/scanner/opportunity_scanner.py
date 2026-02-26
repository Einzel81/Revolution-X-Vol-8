from __future__ import annotations

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.trading_engine import TradingEngine
from app.models.candle import Candle
from app.models.trading_signal import TradingSignal
from app.services.settings_service import SettingsService
from app.scanner.universe import parse_universe, rank_score


class SmartOpportunityScanner:
    def __init__(self, engine: TradingEngine):
        self.engine = engine

    async def _load_candles(self, db: AsyncSession, symbol: str, timeframe: str, limit: int) -> List[Dict[str, Any]]:
        q = (
            select(Candle)
            .where((Candle.symbol == symbol) & (Candle.timeframe == timeframe))
            .order_by(desc(Candle.time))
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        rows = list(reversed(rows))
        return [
            {
                "timestamp": r.time.isoformat(),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in rows
        ]

    async def scan_once(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        settings = SettingsService(db)
        uni_raw = await settings.get("SCANNER_UNIVERSE_JSON")
        uni = parse_universe(uni_raw)

        results: List[Dict[str, Any]] = []

        for s in uni["symbols"]:
            symbol = s["symbol"]
            weight = float(s.get("weight", 1.0))

            for tf in uni["timeframes"]:
                candles = await self._load_candles(db, symbol, tf, int(uni["min_candles"]))
                if len(candles) < int(uni["min_candles"]):
                    continue

                out = await self.engine.analyze_market(
                    data=candles,
                    symbol=symbol,
                    timeframe=tf,
                    extra_context=None,
                    db=db,  # ??? ??? AI registry inference
                )

                sig = out.get("signal") or {}
                base_score = float(sig.get("score") or 0.0)
                adj_score = rank_score(base_score, weight)

                row = TradingSignal(
                    user_id=user_id,
                    source="scanner",
                    symbol=symbol,
                    timeframe=tf,
                    action=str(sig.get("action") or "NEUTRAL"),
                    confidence=float(sig.get("confidence") or 0.0),
                    score=float(adj_score),
                    entry_price=sig.get("entry_price"),
                    suggested_sl=sig.get("suggested_sl"),
                    suggested_tp=sig.get("suggested_tp"),
                    context=sig.get("adaptive"),
                )
                db.add(row)

                # flush to get row.id before commit
                await db.flush()

                results.append(
                    {
                        "signal_id": str(row.id),
                        "symbol": symbol,
                        "timeframe": tf,
                        "action": row.action,
                        "score": float(row.score or 0.0),
                        "confidence": float(row.confidence or 0.0),
                        "weight": weight,
                    }
                )

        await db.commit()

        results.sort(key=lambda x: x["score"], reverse=True)
        top_k = int(uni.get("top_k", uni.get("top_k", 10)) or 10)

        return {"count": len(results), "top": results[:top_k]}