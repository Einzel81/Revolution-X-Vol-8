from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database.connection import get_db
from app.auth.dependencies import require_trader
from app.models.trading_signal import TradingSignal
from app.core.trading_engine import TradingEngine
from app.scanner.opportunity_scanner import SmartOpportunityScanner
from app.scanner.execution_service import ScannerExecutionService

router = APIRouter(prefix="/scanner", tags=["scanner"])

_engine = TradingEngine()
_scanner = SmartOpportunityScanner(_engine)


@router.post("/run")
async def run_scan(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    return await _scanner.scan_once(db=db, user_id=str(user.id))


@router.get("/recent")
async def recent_scanner_signals(
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_trader),
):
    q = (
        select(TradingSignal)
        .where(TradingSignal.source == "scanner")
        .order_by(desc(TradingSignal.created_at))
        .limit(limit)
    )
    if symbol:
        q = q.where(TradingSignal.symbol == symbol)
    if timeframe:
        q = q.where(TradingSignal.timeframe == timeframe)

    rows = (await db.execute(q)).scalars().all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(r.id),
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "action": r.action,
                "score": r.score,
                "confidence": r.confidence,
                "entry_price": r.entry_price,
                "suggested_sl": r.suggested_sl,
                "suggested_tp": r.suggested_tp,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.post("/execute/{signal_id}")
async def execute_scanner_signal(signal_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    # TODO: replace with real account balance retrieval
    balance = 12450.0
    out = await ScannerExecutionService.execute_signal_by_id(db=db, signal_id=signal_id, user_id=str(user.id), balance=balance)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out)
    return out


@router.post("/execute-best")
async def execute_best_scanner_signal(
    min_score: float = 65,
    min_confidence: float = 70,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_trader),
):
    # TODO: replace with real account balance retrieval
    balance = 12450.0
    out = await ScannerExecutionService.execute_best(
        db=db,
        user_id=str(user.id),
        balance=balance,
        min_score=min_score,
        min_confidence=min_confidence,
        enforce_limits=True,
    )
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out)
    return out