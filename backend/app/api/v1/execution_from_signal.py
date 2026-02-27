from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import get_db
from app.auth.dependencies import require_trader
from app.models.trading_signal import TradingSignal
from app.api.v1.trading import trading_engine
from app.mt5.connector import mt5_connector


async def _get_live_balance() -> float:
    fn = getattr(mt5_connector, "account_info", None)
    if not callable(fn):
        raise HTTPException(status_code=501, detail="mt5_connector.account_info not implemented")

    resp = fn()
    if hasattr(resp, "__await__"):
        resp = await resp
    if isinstance(resp, dict) and resp.get("error"):
        raise HTTPException(status_code=503, detail={"ok": False, "error": resp.get("error")})

    data = resp
    if isinstance(resp, dict) and isinstance(resp.get("data"), dict):
        data = resp["data"]
    if isinstance(resp, dict) and isinstance(resp.get("response"), dict):
        data = resp["response"]

    bal = data.get("balance") if isinstance(data, dict) else None
    if bal is None and isinstance(data, dict):
        bal = data.get("equity")
    try:
        bal_f = float(bal)
    except Exception:
        raise HTTPException(status_code=503, detail={"ok": False, "error": "unable_to_parse_balance", "raw": resp})
    if bal_f <= 0:
        raise HTTPException(status_code=503, detail={"ok": False, "error": "invalid_balance", "raw": resp})
    return bal_f

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
        balance=await _get_live_balance(),
        db=db,
        user_id=str(user.id),
        symbol=sig.symbol,
        timeframe=sig.timeframe,
    )