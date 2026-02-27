from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.executor import execution_executor


@dataclass
class TWAPPlan:
    slices: int
    interval_ms: int


class AdvancedExecutionAlgos:
    """Advanced execution algorithms (Vol-8): TWAP only."""

    async def twap(
        self,
        *,
        db: AsyncSession,
        user_id: Optional[str],
        source: str,
        symbol: str,
        side: str,
        total_volume: float,
        sl: Optional[float],
        tp: Optional[float],
        requested_price: Optional[float],
        plan: TWAPPlan,
    ) -> Dict[str, Any]:
        slices = max(1, int(plan.slices))
        interval_ms = max(0, int(plan.interval_ms))

        slice_vol = float(total_volume) / float(slices)
        results: List[Dict[str, Any]] = []

        for i in range(slices):
            r = await execution_executor.execute(
                db=db,
                user_id=user_id,
                source=f"{source}:twap:{i+1}/{slices}",
                symbol=symbol,
                side=side,
                volume=slice_vol,
                sl=sl,
                tp=tp,
                requested_price=requested_price,
                is_automation=("auto_select" in source),
            )
            results.append(r)

            if r.get("status") in ("error", "blocked"):
                break

            if interval_ms > 0 and i < slices - 1:
                await asyncio.sleep(interval_ms / 1000.0)

        return {
            "algo": "TWAP",
            "symbol": symbol,
            "side": side,
            "total_volume": float(total_volume),
            "slices": slices,
            "interval_ms": interval_ms,
            "results": results,
            "ok": all(x.get("status") not in ("error", "blocked") for x in results),
        }


advanced_execution_algos = AdvancedExecutionAlgos()