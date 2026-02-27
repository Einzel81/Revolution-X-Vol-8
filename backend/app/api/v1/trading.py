# backend/app/api/v1/trading.py (???????)
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Any, Dict, List

from app.database.connection import get_db
from app.core.trading_engine import TradingEngine
from app.auth.dependencies import get_current_user, require_trader
from app.models.trade import Trade
from app.services.activity_bus import publish_activity
from app.mt5.connector import mt5_connector

router = APIRouter()

# Initialize trading engine
trading_engine = TradingEngine()

@router.get("/status")
async def trading_status(
    current_user = Depends(require_trader)
):
    """Get trading system status"""
    return {
        "status": "active",
        "mode": "auto_scaling",
        "is_running": trading_engine.is_running,
        "open_positions": 0,  # TODO: Get from DB
        "daily_pnl": 0.0,
        "risk_status": trading_engine.risk_manager.get_risk_report()
    }

@router.get("/balance")
async def get_balance(
    current_user = Depends(require_trader)
):
    """Get account balance"""
    fn = getattr(mt5_connector, "account_info", None)
    if not callable(fn):
        return {"ok": False, "error": "mt5_connector.account_info not implemented"}

    resp = fn()
    if hasattr(resp, "__await__"):
        resp = await resp
    if isinstance(resp, dict) and resp.get("error"):
        return {"ok": False, "error": resp.get("error"), "raw": resp}

    data = resp
    if isinstance(resp, dict) and isinstance(resp.get("data"), dict):
        data = resp["data"]
    if isinstance(resp, dict) and isinstance(resp.get("response"), dict):
        data = resp["response"]

    return {
        "ok": True,
        "balance": (data.get("balance") if isinstance(data, dict) else None),
        "equity": (data.get("equity") if isinstance(data, dict) else None),
        "margin": (data.get("margin") if isinstance(data, dict) else None),
        "free_margin": (data.get("free_margin") if isinstance(data, dict) else None),
        "margin_level": (data.get("margin_level") if isinstance(data, dict) else None),
        "raw": resp,
    }

@router.post("/analyze")
async def analyze_market(
    symbol: str = "XAUUSD",
    timeframe: str = "M15",
    current_user = Depends(require_trader)
):
    """
    Run full market analysis
    """
    # TODO: Get real data from MT5
    # For now, return mock data structure
    import random
    from datetime import datetime, timedelta
    
    # Generate mock OHLCV data
    base_price = 2945.50
    data = []
    for i in range(100):
        timestamp = datetime.utcnow() - timedelta(minutes=15*(100-i))
        open_p = base_price + random.uniform(-10, 10)
        close_p = open_p + random.uniform(-5, 5)
        high_p = max(open_p, close_p) + random.uniform(0, 3)
        low_p = min(open_p, close_p) - random.uniform(0, 3)
        
        data.append({
            "timestamp": timestamp.isoformat(),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": random.randint(1000, 5000)
        })
    
    # Run analysis
    result = await trading_engine.analyze_market(data, symbol)
    
    return result

@router.post("/signal")
async def get_signal(
    symbol: str = "XAUUSD",
    current_user = Depends(require_trader)
):
    """Get current trading signal"""
    # Mock signal for now
    return {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat(),
        "signal": {
            "action": "BUY",
            "confidence": 75,
            "score": 45,
            "reasons": [
                "Strong bullish OB at 2940.50",
                "Price below value area",
                "Bullish trend"
            ],
            "entry_price": 2945.50,
            "suggested_sl": 2920.00,
            "suggested_tp": 2995.00,
            "kill_zone": {
                "can_trade": True,
                "session": "london_ny_overlap",
                "volatility": 5,
                "liquidity": 5
            }
        }
    }

@router.post("/execute")
async def execute_trade(
    symbol: str = "XAUUSD",
    action: str = "BUY",
    entry: float = 2945.50,
    sl: float = 2920.00,
    tp: float = 2995.00,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_trader),
):
    """Execute a trade.

    - Applies RiskManager + position sizing (Kelly-based) from TradingEngine
    - Delegates live/paper execution to execution_executor
    """
    side = action.upper().strip()
    if side not in {"BUY", "SELL"}:
        return {"status": "error", "reason": "action must be BUY or SELL"}

    signal = {
        "action": side,
        "entry_price": float(entry),
        "suggested_sl": float(sl),
        "suggested_tp": float(tp),
        "confidence": 75,
    }

    # Pull real balance (best-effort). If unavailable, refuse live sizing.
    bal = None
    try:
        info = await mt5_connector.account_info()
        data = info
        if isinstance(info, dict) and isinstance(info.get("data"), dict):
            data = info["data"]
        if isinstance(info, dict) and isinstance(info.get("response"), dict):
            data = info["response"]
        if isinstance(data, dict):
            bal = data.get("balance") or data.get("equity")
    except Exception:
        bal = None
    if bal is None:
        return {"status": "error", "reason": "unable_to_fetch_balance_from_mt5"}

    # Use engine end-to-end (risk+sizing+execution+logs)
    res = await trading_engine.execute_trade(
        signal=signal,
        balance=float(bal),
        db=db,
        user_id=str(current_user.id),
        symbol=symbol.upper(),
        timeframe=None,
    )

    exec_res = res.get("execution") or {}
    lots = float((res.get("position_size") or {}).get("lots") or 0.0)

    # Broadcast activity (best-effort)
    try:
        await publish_activity(
            "activity",
            {
                "event": "execution",
                "symbol": symbol.upper(),
                "side": side,
                "volume": lots,
                "status": res.get("status"),
                "slippage": exec_res.get("slippage"),
                "latency_ms": exec_res.get("latency_ms"),
            },
        )
    except Exception:
        pass

    return res

@router.get("/positions")
async def get_positions(
    current_user = Depends(require_trader)
):
    """Get open positions"""
    # Frontend expects a LIST of positions.
    # MT5 snapshots ingestion is not enabled by default in Vol-8, so return empty list.
    return []


@router.get("/trades")
async def get_trades(
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_trader),
):
    """Return trade history as a flat list (frontend-friendly)."""
    q = (
        select(Trade)
        .where(Trade.user_id == current_user.id)
        .order_by(desc(Trade.open_time))
        .limit(int(limit))
    )
    rows = (await db.execute(q)).scalars().all()

    out: List[Dict[str, Any]] = []
    for t in rows:
        out.append(
            {
                "id": str(t.id),
                "symbol": t.symbol,
                "type": str(t.type.value if hasattr(t.type, "value") else t.type),
                "entryPrice": t.entry_price,
                "exitPrice": t.exit_price,
                "volume": t.volume,
                "openTime": t.open_time.isoformat() if t.open_time else None,
                "closeTime": t.close_time.isoformat() if t.close_time else None,
                "pnl": t.profit or 0.0,
                "status": str(t.status.value if hasattr(t.status, "value") else t.status),
                "stopLoss": t.stop_loss,
                "takeProfit": t.take_profit,
            }
        )
    return out

@router.post("/positions/{position_id}/close")
async def close_position(
    position_id: str,
    current_user = Depends(require_trader)
):
    """Close a position"""
    return {"status": "success", "position_id": position_id}