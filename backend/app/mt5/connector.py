import asyncio
import time
from typing import Any, Dict, Optional

import zmq
import zmq.asyncio

from app.config import settings


class MT5Connector:
    def __init__(self):
        self.context = zmq.asyncio.Context()
        self.socket = None
        self.connected = False
        self.host = getattr(settings, "MT5_HOST", "localhost")
        self.port = int(getattr(settings, "MT5_PORT", 9000))

    def set_endpoint(self, host: str, port: int) -> None:
        host = str(host).strip()
        port = int(port)
        if host and (host != self.host or port != self.port):
            self.host = host
            self.port = port
            self.connected = False
            try:
                if self.socket is not None:
                    self.socket.close(linger=0)
            except Exception:
                pass
            self.socket = None

    async def connect(self):
        try:
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect(f"tcp://{self.host}:{self.port}")
            self.connected = True
            return True
        except Exception as e:
            print(f"MT5 Connection Error: {e}")
            self.connected = False
            return False

    async def _ensure(self) -> None:
        if not self.connected or self.socket is None:
            await self.connect()

    async def _call(self, payload: Dict[str, Any], *, timeout_ms: int = 2000) -> Dict[str, Any]:
        await self._ensure()
        try:
            self.socket.send_json(payload)
            resp = await asyncio.wait_for(self.socket.recv_json(), timeout=timeout_ms / 1000)
            if isinstance(resp, dict):
                return resp
            return {"ok": True, "response": resp}
        except Exception as e:
            self.connected = False
            return {"error": str(e)}

    async def ping(self, timeout_ms: int = 800) -> dict:
        try:
            t0 = time.perf_counter()
            resp = await self._call({"action": "PING"}, timeout_ms=timeout_ms)
            if isinstance(resp, dict) and resp.get("error"):
                raise RuntimeError(resp["error"])
            return {"ok": True, "latency_ms": (time.perf_counter() - t0) * 1000.0, "response": resp}
        except Exception:
            t0 = time.perf_counter()
            try:
                resp = await self._call({"action": "ACCOUNT_INFO"}, timeout_ms=timeout_ms)
                if isinstance(resp, dict) and resp.get("error"):
                    raise RuntimeError(resp["error"])
                return {"ok": True, "latency_ms": (time.perf_counter() - t0) * 1000.0, "response": resp, "fallback": True}
            except Exception as e:
                self.connected = False
                return {"ok": False, "error": str(e)}

    async def send_order(
        self,
        symbol: str,
        action: str,
        volume: float,
        sl: Optional[float],
        tp: Optional[float],
        *,
        timeout_ms: int = 2000,
    ) -> Dict[str, Any]:
        order: Dict[str, Any] = {
            "action": "SEND_ORDER",
            "symbol": symbol,
            "type": action,
            "volume": float(volume),
            "sl": sl,
            "tp": tp,
        }
        return await self._call(order, timeout_ms=timeout_ms)

    async def account_info(self, *, timeout_ms: int = 2000) -> Dict[str, Any]:
        """Return account snapshot from bridge.

        Supports multiple common action names used by MT5 bridges.
        """
        # Prefer the canonical action used elsewhere in this repo
        resp = await self._call({"action": "ACCOUNT_INFO"}, timeout_ms=timeout_ms)
        if isinstance(resp, dict) and resp.get("error"):
            # Some bridges use GET_ACCOUNT
            resp2 = await self._call({"action": "GET_ACCOUNT"}, timeout_ms=timeout_ms)
            if not (isinstance(resp2, dict) and resp2.get("error")):
                return resp2
        return resp

    async def get_orders(self, *, timeout_ms: int = 2500) -> Dict[str, Any]:
        """Return pending orders from bridge (if supported)."""
        resp = await self._call({"action": "GET_ORDERS"}, timeout_ms=timeout_ms)
        if isinstance(resp, dict) and resp.get("error"):
            resp2 = await self._call({"action": "ORDERS"}, timeout_ms=timeout_ms)
            if not (isinstance(resp2, dict) and resp2.get("error")):
                return resp2
        return resp

    async def get_positions(self, *, timeout_ms: int = 2500) -> Dict[str, Any]:
        # Support multiple action names
        resp = await self._call({"action": "GET_POSITIONS"}, timeout_ms=timeout_ms)
        if isinstance(resp, dict) and resp.get("error"):
            resp2 = await self._call({"action": "POSITIONS"}, timeout_ms=timeout_ms)
            if not (isinstance(resp2, dict) and resp2.get("error")):
                return resp2
        return resp

    async def get_rates(self, symbol: str, timeframe: str, count: int = 300, *, timeout_ms: int = 3500) -> Dict[str, Any]:
        return await self._call({"action": "RATES", "symbol": symbol, "timeframe": timeframe, "count": int(count)}, timeout_ms=timeout_ms)


mt5_connector = MT5Connector()