from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.auth.dependencies import require_trader
from app.market_data.dxy_tracker import get_cached_dxy_context

# shared TradingEngine instance
from .trading import trading_engine


router = APIRouter()


class Candle(BaseModel):
    timestamp: Optional[str] = None
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class AdaptiveRouteRequest(BaseModel):
    symbol: str = "XAUUSD"
    candles: List[Candle] = Field(..., min_items=20)
    # Optional manual override
    dxy: Optional[Dict[str, Any]] = None


@router.post("/route")
async def adaptive_route(req: AdaptiveRouteRequest, _=Depends(require_trader)):
    data = [c.model_dump() for c in req.candles]

    # DXY priority: request override -> cached
    dxy_ctx = req.dxy if req.dxy else get_cached_dxy_context()

    result = await trading_engine.analyze_market(
        data=data,
        symbol=req.symbol,
        extra_context={"dxy": dxy_ctx} if dxy_ctx else None,
    )

    return {"symbol": req.symbol, "signal": result.get("signal")}


@router.post("/scores")
async def adaptive_scores(req: AdaptiveRouteRequest, _=Depends(require_trader)):
    """
    Always returns adaptive table (regime + scores) even if action is NEUTRAL/WAIT.
    """
    data = [c.model_dump() for c in req.candles]
    dxy_ctx = req.dxy if req.dxy else get_cached_dxy_context()

    result = await trading_engine.analyze_market(
        data=data,
        symbol=req.symbol,
        extra_context={"dxy": dxy_ctx} if dxy_ctx else None,
    )

    signal = result.get("signal") or {}
    adaptive = (signal.get("adaptive") or {})
    return {
        "symbol": req.symbol,
        "action": signal.get("action"),
        "score": signal.get("score"),
        "confidence": signal.get("confidence"),
        "adaptive": adaptive,
    }


@router.get("/dxy")
async def dxy_status(_=Depends(require_trader)):
    """
    Dashboard endpoint: show latest cached DXY context.
    """
    return {"dxy": get_cached_dxy_context()}