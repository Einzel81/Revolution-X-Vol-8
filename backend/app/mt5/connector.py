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

    def _endpoint(self) -> str:
        return f"tcp://{self.host}:{self.port}"

    def _err(self, e: Exception, prefix: str = "mt5_error") -> Dict[str, Any]:
        msg = str(e).strip()
        if not msg:
            msg = f"{type(e).__name__}"
        else:
            msg = f"{type(e).__name__}: {msg}"
        return {"ok": False, "error": msg, "where": prefix, "endpoint": self._endpoint()}

    async def connect(self) -> bool:
        try:
            # Close previous
            try:
                if self.socket is not None:
                    self.socket.close(linger=0)
            except Exception:
                pass

            self.socket = self.context.socket(zmq.REQ)
            self.socket.linger = 0  # important for quick reconnects
            self.socket.connect(self._endpoint())
            self.connected = True
            return True
        except Exception as e:
            print(f"MT5 Connection Error: {e}")
            self.connected = False
            return False

    async def _ensure(self) -> bool:
        if not self.connected or self.socket is None:
            return await self.connect()
        return True

    async def _call(self, payload: Dict[str, Any], *, timeout_ms: int = 2000) -> Dict[str, Any]:
        ok = await self._ensure()
        if not ok or self.socket is None:
            return {"ok": False, "error": "mt5_not_connected", "endpoint": self._endpoint()}

        try:
            await self.socket.send_json(payload)
            resp = await asyncio.wait_for(self.socket.recv_json(), timeout=timeout_ms / 1000)
            if isinstance(resp, dict):
                # Attach endpoint for easier debugging
                if "endpoint" not in resp:
                    resp["endpoint"] = self._endpoint()
                return resp
            return {"ok": True, "response": resp, "endpoint": self._endpoint()}
        except Exception as e:
            self.connected = False
            return self._err(e, prefix=f"call:{payload.get('action')}")

    async def ping(self, timeout_ms: int = 800) -> dict:
        try:
            t0 = time.perf_counter()
            resp = await self._call({"action": "PING"}, timeout_ms=timeout_ms)
            if isinstance(resp, dict) and resp.get("error"):
                raise RuntimeError(str(resp.get("error")))
            return {"ok": True, "latency_ms": (time.perf_counter() - t0) * 1000.0, "response": resp, "endpoint": self._endpoint()}
        except Exception:
            t0 = time.perf_counter()
            try:
                resp = await self._call({"action": "ACCOUNT_INFO"}, timeout_ms=timeout_ms)
                if isinstance(resp, dict) and resp.get("error"):
                    raise RuntimeError(str(resp.get("error")))
                return {"ok": True, "latency_ms": (time.perf_counter() - t0) * 1000.0, "response": resp, "fallback": True, "endpoint": self._endpoint()}
            except Exception as e:
                self.connected = False
                out = self._err(e, prefix="ping")
                out["latency_ms"] = (time.perf_counter() - t0) * 1000.0
                return out

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
        resp = await self._call({"action": "ACCOUNT_INFO"}, timeout_ms=timeout_ms)
        if isinstance(resp, dict) and resp.get("error"):
            resp2 = await self._call({"action": "GET_ACCOUNT"}, timeout_ms=timeout_ms)
            if not (isinstance(resp2, dict) and resp2.get("error")):
                return resp2
        return resp

    async def get_orders(self, *, timeout_ms: int = 2500) -> Dict[str, Any]:
        resp = await self._call({"action": "GET_ORDERS"}, timeout_ms=timeout_ms)
        if isinstance(resp, dict) and resp.get("error"):
            resp2 = await self._call({"action": "ORDERS"}, timeout_ms=timeout_ms)
            if not (isinstance(resp2, dict) and resp2.get("error")):
                return resp2
        return resp

    async def get_positions(self, *, timeout_ms: int = 2500) -> Dict[str, Any]:
        resp = await self._call({"action": "GET_POSITIONS"}, timeout_ms=timeout_ms)
        if isinstance(resp, dict) and resp.get("error"):
            resp2 = await self._call({"action": "POSITIONS"}, timeout_ms=timeout_ms)
            if not (isinstance(resp2, dict) and resp2.get("error")):
                return resp2
        return resp

    async def get_rates(self, symbol: str, timeframe: str, count: int = 300, *, timeout_ms: int = 3500) -> Dict[str, Any]:
        return await self._call(
            {"action": "RATES", "symbol": symbol, "timeframe": timeframe, "count": int(count)},
            timeout_ms=timeout_ms,
        )


mt5_connector = MT5Connector()