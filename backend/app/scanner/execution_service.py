from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.trading_signal import TradingSignal
from app.services.settings_service import SettingsService

# trading_engine is the existing execution entry in your project
from app.api.v1.trading import trading_engine


class ScannerExecutionService:
    """
    Service-level execution for scanner signals:
    - no Depends()
    - can be called from API endpoints or Celery tasks
    """

    @staticmethod
    async def _count_trades_last_hour(db: AsyncSession, user_id: str) -> int:
        """
        Counts executions in last hour using ExecutionLog if present,
        otherwise falls back to Trades table if available.
        """
        since = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

        # Prefer ExecutionEvent (has user_id and stores every attempt)
        try:
            from app.models.execution_event import ExecutionEvent  # type: ignore

            q = select(func.count(ExecutionEvent.id)).where(
                (ExecutionEvent.user_id == str(user_id)) & (ExecutionEvent.created_at >= since)
            )
            n = (await db.execute(q)).scalar_one()
            return int(n or 0)
        except Exception:
            pass

        # Fallback: Trade table (filled trades)
        try:
            from app.models.trade import Trade  # type: ignore

            q = select(func.count(Trade.id)).where((Trade.user_id == user_id) & (Trade.created_at >= since))
            n = (await db.execute(q)).scalar_one()
            return int(n or 0)
        except Exception:
            return 0

    @staticmethod
    async def _pick_best_signal(
        db: AsyncSession,
        symbol: Optional[str],
        timeframe: Optional[str],
        min_score: float,
        min_confidence: float,
    ) -> Optional[TradingSignal]:
        q = (
            select(TradingSignal)
            .where(
                (TradingSignal.source == "scanner")
                & (TradingSignal.action.in_(["BUY", "SELL"]))
                & (TradingSignal.score != None)
                & (TradingSignal.confidence != None)
                & (TradingSignal.score >= min_score)
                & (TradingSignal.confidence >= min_confidence)
            )
            .order_by(desc(TradingSignal.score), desc(TradingSignal.created_at))
            .limit(1)
        )
        if symbol:
            q = q.where(TradingSignal.symbol == symbol)
        if timeframe:
            q = q.where(TradingSignal.timeframe == timeframe)

        return (await db.execute(q)).scalar_one_or_none()

    @staticmethod
    async def execute_signal_by_id(
        db: AsyncSession,
        signal_id: str,
        user_id: str,
        balance: float,
    ) -> Dict[str, Any]:
        sig = (await db.execute(select(TradingSignal).where(TradingSignal.id == signal_id))).scalar_one_or_none()
        if not sig:
            return {"ok": False, "error": "signal_not_found"}

        if sig.action not in ("BUY", "SELL"):
            return {"ok": False, "error": "signal_not_executable", "action": sig.action}

        payload = {
            "action": sig.action,
            "entry_price": sig.entry_price,
            "suggested_sl": sig.suggested_sl,
            "suggested_tp": sig.suggested_tp,
            "confidence": sig.confidence,
            "score": sig.score,
            "reasons": ["scanner_execute"],
            "adaptive": sig.context,
        }

        result = await trading_engine.execute_trade(
            signal=payload,
            balance=balance,
            db=db,
            user_id=user_id,
            symbol=sig.symbol,
            timeframe=sig.timeframe,
        )
        return {"ok": True, "signal_id": str(sig.id), "symbol": sig.symbol, "timeframe": sig.timeframe, "result": result}

    @staticmethod
    async def execute_best(
        db: AsyncSession,
        user_id: str,
        balance: float,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        min_score: Optional[float] = None,
        min_confidence: Optional[float] = None,
        enforce_limits: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes best eligible scanner signal.
        Enforces:
          - AUTO_SELECT_MAX_TRADES_PER_HOUR (if enforce_limits)
        Reads defaults from settings if not provided.
        """
        settings = SettingsService(db)

        if min_score is None:
            min_score = float(await settings.get("AUTO_SELECT_MIN_SCORE") or 65)
        if min_confidence is None:
            min_confidence = float(await settings.get("AUTO_SELECT_MIN_CONFIDENCE") or 70)

        if enforce_limits:
            max_per_hour = int(await settings.get("AUTO_SELECT_MAX_TRADES_PER_HOUR") or 2)
            n = await ScannerExecutionService._count_trades_last_hour(db, user_id)
            if n >= max_per_hour:
                return {"ok": False, "error": "rate_limited", "trades_last_hour": n, "max_per_hour": max_per_hour}

        sig = await ScannerExecutionService._pick_best_signal(
            db=db,
            symbol=symbol,
            timeframe=timeframe,
            min_score=float(min_score),
            min_confidence=float(min_confidence),
        )
        if not sig:
            return {
                "ok": False,
                "error": "no_eligible_signal",
                "min_score": float(min_score),
                "min_confidence": float(min_confidence),
            }

        payload = {
            "action": sig.action,
            "entry_price": sig.entry_price,
            "suggested_sl": sig.suggested_sl,
            "suggested_tp": sig.suggested_tp,
            "confidence": sig.confidence,
            "score": sig.score,
            "reasons": ["scanner_execute_best"],
            "adaptive": sig.context,
        }

        result = await trading_engine.execute_trade(
            signal=payload,
            balance=balance,
            db=db,
            user_id=user_id,
            symbol=sig.symbol,
            timeframe=sig.timeframe,
        )

        return {
            "ok": True,
            "signal_id": str(sig.id),
            "symbol": sig.symbol,
            "timeframe": sig.timeframe,
            "score": float(sig.score or 0),
            "confidence": float(sig.confidence or 0),
            "result": result,
        }