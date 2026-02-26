from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.mt5.connector import mt5_connector
from app.models.execution_event import ExecutionEvent
from app.config import settings


def _parse_fill(resp: Any) -> Tuple[Optional[str], Optional[float]]:
    """Extract (ticket, fill_price) from common bridge responses."""
    if not isinstance(resp, dict):
        return None, None
    ticket = resp.get("ticket") or resp.get("order") or resp.get("deal") or resp.get("id")
    fill_price = resp.get("fill_price") or resp.get("filled_price") or resp.get("price")
    try:
        fill_price = float(fill_price) if fill_price is not None else None
    except Exception:
        fill_price = None
    return (str(ticket) if ticket is not None else None), fill_price


def _calc_slippage(side: str, requested: Optional[float], filled: Optional[float]) -> Optional[float]:
    if requested is None or filled is None:
        return None
    side_u = side.upper()
    if side_u == "BUY":
        return float(filled - requested)
    if side_u == "SELL":
        return float(requested - filled)
    return None


@dataclass
class ExecutionGuards:
    max_slippage: float
    max_latency_ms: float


class ExecutionExecutor:
    """Live execution + telemetry.

    - Measures latency
    - Estimates slippage when fill price is returned
    - Blocks execution if guards are violated (latency / slippage)
    - Stores every attempt into execution_events
    """

    def __init__(self):
        self.guards = ExecutionGuards(
            max_slippage=float(getattr(settings, "EXEC_MAX_SLIPPAGE", 2.5)),
            max_latency_ms=float(getattr(settings, "EXEC_MAX_LATENCY_MS", 1500)),
        )

    async def execute(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        source: str,
        symbol: str,
        side: str,
        volume: float,
        sl: Optional[float],
        tp: Optional[float],
        requested_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        side = side.upper()
        mode = str(getattr(settings, "TRADING_MODE", "paper")).lower()
        bridge = str(getattr(settings, "EXECUTION_BRIDGE", "simulated")).lower()

        # Paper mode or simulated bridge => no live execution
        if mode != "live" or bridge != "mt5_zmq":
            ev = ExecutionEvent(
                user_id=str(user_id) if user_id else None,
                source=source,
                symbol=symbol,
                side=side,
                volume=float(volume),
                requested_price=requested_price,
                sl=sl,
                tp=tp,
                status="simulated",
                bridge_connected=False,
                request={"mode": mode, "bridge": bridge},
                response={"note": "simulated execution"},
            )
            db.add(ev)
            await db.commit()
            return {"status": "simulated", "symbol": symbol, "side": side, "volume": volume}

        # Live execution
        t0 = time.perf_counter()
        req = {"symbol": symbol, "type": side, "volume": volume, "sl": sl, "tp": tp}

        resp = await mt5_connector.send_order(
            symbol=symbol,
            action=side,
            volume=volume,
            sl=sl,
            tp=tp,
            timeout_ms=int(getattr(settings, "EXEC_TIMEOUT_MS", 2000)),
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Bridge may return {error: ...}
        if isinstance(resp, dict) and resp.get("error"):
            ev = ExecutionEvent(
                user_id=str(user_id) if user_id else None,
                source=source,
                symbol=symbol,
                side=side,
                volume=float(volume),
                requested_price=requested_price,
                sl=sl,
                tp=tp,
                status="error",
                bridge_connected=False,
                latency_ms=latency_ms,
                error=str(resp.get("error")),
                request=req,
                response=resp,
            )
            db.add(ev)
            await db.commit()
            return {"status": "error", "error": str(resp.get("error")), "latency_ms": latency_ms}

        ticket, fill_price = _parse_fill(resp)
        slippage = _calc_slippage(side, requested_price, fill_price)

        # Guards
        if latency_ms > self.guards.max_latency_ms:
            status = "blocked"
            reason = f"latency_ms={latency_ms:.0f} > max={self.guards.max_latency_ms:.0f}"
        elif slippage is not None and abs(slippage) > self.guards.max_slippage:
            status = "blocked"
            reason = f"slippage={slippage:.2f} > max={self.guards.max_slippage:.2f}"
        else:
            status = "success"
            reason = None

        ev = ExecutionEvent(
            user_id=str(user_id) if user_id else None,
            source=source,
            symbol=symbol,
            side=side,
            volume=float(volume),
            requested_price=requested_price,
            sl=sl,
            tp=tp,
            status=status,
            ticket=ticket,
            fill_price=fill_price,
            slippage=slippage,
            latency_ms=latency_ms,
            bridge_connected=bool(getattr(mt5_connector, "connected", False)),
            error=reason,
            request=req,
            response=resp if isinstance(resp, dict) else {"raw": str(resp)},
        )
        db.add(ev)
        await db.commit()

        return {
            "status": status,
            "reason": reason,
            "ticket": ticket,
            "fill_price": fill_price,
            "slippage": slippage,
            "latency_ms": latency_ms,
            "bridge_connected": bool(getattr(mt5_connector, "connected", False)),
            "raw": resp,
        }


execution_executor = ExecutionExecutor()