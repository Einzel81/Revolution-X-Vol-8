from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import get_db
from app.auth.dependencies import require_trader
from app.models.trading_signal import TradingSignal
from app.api.v1.trading import trading_engine

router = APIRouter(prefix="/scanner", tags=["scanner"])

@router.post("/execute/{signal_id}")
async def execute_scanner_signal(signal_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    row = await db.execute(
        select(TradingSignal).where(TradingSignal.id == signal_id)
    )
    sig = row.scalar_one_or_none()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")

    if sig.action not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="Signal action is not executable")

    signal_payload = {
        "action": sig.action,
        "entry_price": sig.entry_price,
        "suggested_sl": sig.suggested_sl,
        "suggested_tp": sig.suggested_tp,
        "confidence": sig.confidence,
        "score": sig.score,
        "reasons": ["scanner_execute_button"],
        "adaptive": sig.context,
    }

    # execute_trade already persists Signal/Trade/ExecutionLogs if db+user_id passed
    return await trading_engine.execute_trade(
        signal=signal_payload,
        balance=12450.0,  # TODO: pull real balance
        db=db,
        user_id=str(user.id),
        symbol=sig.symbol,
        timeframe=sig.timeframe,
    )