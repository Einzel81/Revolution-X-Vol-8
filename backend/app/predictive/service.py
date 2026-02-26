from __future__ import annotations

import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.trade import Trade
from app.models.predictive_report import PredictiveReport
from app.services.settings_service import SettingsService


class PredictiveService:
    async def _load_trades(self, db: AsyncSession, symbol: str, limit: int = 4000) -> pd.DataFrame:
        q = (
            select(Trade)
            .where(Trade.symbol == symbol)
            .order_by(desc(Trade.created_at))
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()

        data = []
        for r in rows:
            pnl = getattr(r, "pnl", None)
            t = getattr(r, "created_at", None)
            if pnl is None or t is None:
                continue
            data.append({"time": t, "pnl": float(pnl)})

        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=["time", "pnl"])
        return df.sort_values("time")

    def walk_forward_eval(self, df: pd.DataFrame) -> Dict[str, float]:
        if len(df) < 60:
            return {"sharpe": 0.0, "winrate": 0.0, "avg_return": 0.0}

        rets = df["pnl"].values.astype(float)
        mean = float(np.mean(rets))
        std = float(np.std(rets)) + 1e-9

        # Sharpe ???? ?????? (????? ??? ????? ??????? ???? ???? ???? ????????)
        sharpe = (mean / std) * np.sqrt(252)
        winrate = float(np.sum(rets > 0) / len(rets))
        avg_return = mean

        return {"sharpe": float(sharpe), "winrate": float(winrate), "avg_return": float(avg_return)}

    def monte_carlo_equity(self, df: pd.DataFrame, runs: int = 500) -> Dict[str, float]:
        if len(df) < 60:
            return {"max_dd": 0.0, "var_95": 0.0}

        rets = df["pnl"].values.astype(float)

        end_values = []
        worst_dd = []

        for _ in range(runs):
            shuffled = np.random.permutation(rets)
            equity = np.cumsum(shuffled)

            peak = np.maximum.accumulate(equity)
            dd = equity - peak  # drawdown series (<=0)
            worst_dd.append(float(np.min(dd)))
            end_values.append(float(equity[-1]))

        # ???? DD ??????? + VaR 95% ??? ????? ??????
        return {
            "max_dd": float(np.percentile(worst_dd, 50)),   # median worst-dd
            "var_95": float(np.percentile(end_values, 5)),
        }

    def detect_drift(self, df: pd.DataFrame) -> float:
        if len(df) < 120:
            return 0.0

        mid = len(df) // 2
        a = df["pnl"].values[:mid].astype(float)
        b = df["pnl"].values[mid:].astype(float)

        drift = abs(float(np.mean(a)) - float(np.mean(b)))
        return float(drift)

    def stability_score(self, wf: Dict[str, float], mc: Dict[str, float], drift: float) -> float:
        # Score ?????: ?????? ??????? ????? ??? DD ? drift
        score = 0.0
        score += wf["sharpe"] * 25.0
        score += wf["winrate"] * 100.0
        score += wf["avg_return"] * 10.0
        score -= abs(mc["max_dd"]) * 0.5
        score -= drift * 50.0
        return float(score)

    async def apply_auto_select_gate(self, db: AsyncSession, symbol: str, timeframe: str, stability: float) -> Dict[str, Any]:
        settings = SettingsService(db)

        min_stab = float(await settings.get("PREDICTIVE_STABILITY_MIN") or 120)
        if stability >= min_stab:
            # ?? ????? Auto-Select ???????? (???? ?????) — ??? ?? ?????
            await settings.set("AUTO_SELECT_DISABLE_REASON", None, is_secret=False)
            return {"gate": "pass", "min": min_stab, "stability": stability}

        # Fail => ????? Auto-Select
        await settings.set("AUTO_SELECT_ENABLED", "false", is_secret=False)
        await settings.set(
            "AUTO_SELECT_DISABLE_REASON",
            f"Predictive gate fail: stability={stability:.2f} < min={min_stab:.2f} ({symbol} {timeframe})",
            is_secret=False,
        )
        return {"gate": "fail_disable_auto_select", "min": min_stab, "stability": stability}

    async def run_full_report(self, db: AsyncSession, symbol: str, timeframe: str) -> Dict[str, Any]:
        df = await self._load_trades(db, symbol)

        wf = self.walk_forward_eval(df)
        mc = self.monte_carlo_equity(df)
        drift = self.detect_drift(df)
        stability = self.stability_score(wf, mc, drift)

        report = PredictiveReport(
            symbol=symbol,
            timeframe=timeframe,
            wf_sharpe=wf["sharpe"],
            wf_winrate=wf["winrate"],
            wf_avg_return=wf["avg_return"],
            mc_max_dd=mc["max_dd"],
            mc_var_95=mc["var_95"],
            drift_score=drift,
            stability_score=stability,
            meta={"trades": int(len(df))},
        )
        db.add(report)
        await db.commit()

        gate = await self.apply_auto_select_gate(db, symbol, timeframe, stability)

        return {
            "wf": wf,
            "mc": mc,
            "drift": float(drift),
            "stability_score": float(stability),
            "gate": gate,
            "meta": {"trades": int(len(df))},
        }

    async def latest_report_ok(
        self,
        db: AsyncSession,
        symbol: str,
        timeframe: str,
        max_age_minutes: int
    ) -> Tuple[bool, Optional[PredictiveReport], str]:
        q = (
            select(PredictiveReport)
            .where((PredictiveReport.symbol == symbol) & (PredictiveReport.timeframe == timeframe))
            .order_by(desc(PredictiveReport.created_at))
            .limit(1)
        )
        r = (await db.execute(q)).scalar_one_or_none()
        if not r:
            return False, None, "no_predictive_report"

        age = datetime.datetime.utcnow() - (r.created_at or datetime.datetime.utcnow())
        if age.total_seconds() > max_age_minutes * 60:
            return False, r, f"predictive_report_stale_age_min={age.total_seconds()/60:.1f}"

        return True, r, "ok"