from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database.connection import get_db
from app.auth.dependencies import require_admin
from app.models.predictive_report import PredictiveReport
from app.predictive.service import PredictiveService

router = APIRouter(prefix="/predictive", tags=["predictive"])
service = PredictiveService()


@router.post("/run")
async def run_predictive(symbol: str = "XAUUSD", timeframe: str = "M15",
                         db: AsyncSession = Depends(get_db),
                         user=Depends(require_admin)):
    return await service.run_full_report(db, symbol, timeframe)


@router.get("/latest")
async def latest_predictive(symbol: str = "XAUUSD",
                            db: AsyncSession = Depends(get_db),
                            user=Depends(require_admin)):
    q = (
        select(PredictiveReport)
        .where(PredictiveReport.symbol == symbol)
        .order_by(desc(PredictiveReport.created_at))
        .limit(1)
    )
    r = (await db.execute(q)).scalar_one_or_none()
    if not r:
        return {"message": "No report"}

    return {
        "wf_sharpe": r.wf_sharpe,
        "wf_winrate": r.wf_winrate,
        "wf_avg_return": r.wf_avg_return,
        "mc_max_dd": r.mc_max_dd,
        "mc_var_95": r.mc_var_95,
        "drift_score": r.drift_score,
        "stability_score": r.stability_score,
        "meta": r.meta,
        "created_at": r.created_at,
    }