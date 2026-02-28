import asyncio
import json
import time
from typing import Any, Dict, Optional, Tuple

from app.config import settings


class MT5Connector:
    """TCP JSON Line connector for MT5 EA Bridge.

    This project uses a custom MT5 EA Bridge (RevolutionX_EA_Bridge.mq5) that:
      - Listens on TCP (default 9000)
      - Expects newline-delimited JSON
      - Requires a shared token on every request: { "token": "<BRIDGE_TOKEN>", ... }

    Important:
      - The EA accepts ONE client at a time (listen backlog=1) and keeps the socket open.
      - We therefore keep a single persistent connection and reconnect on any error/timeout.
    """

    def __init__(self) -> None:
        self.connected: bool = False
        self.host: str = str(getattr(settings, "MT5_HOST", "localhost"))
        self.port: int = int(getattr(settings, "MT5_PORT", 9000))

        # EA token (required by bridge)
        self.token: str = str(getattr(settings, "MT5_BRIDGE_TOKEN", "") or "")

        # Async stream state
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

        # Serialize calls: EA is single-client, single-request at a time.
        self._lock = asyncio.Lock()

    def set_endpoint(self, host: str, port: int) -> None:
        host = str(host).strip()
        port = int(port)
        if host and (host != self.host or port != self.port):
            self.host = host
            self.port = port
            self.connected = False
            self._close()

    def set_token(self, token: str) -> None:
        token = str(token or "").strip()
        if token != self.token:
            self.token = token
            # No need to reconnect, but safe to do so if auth changes.
            self.connected = False
            self._close()

    def _endpoint(self) -> str:
        return f"tcp://{self.host}:{self.port}"

    def _close(self) -> None:
        try:
            if self._writer is not None:
                self._writer.close()
        except Exception:
            pass
        self._reader = None
        self._writer = None

    def _err(self, e: Exception, prefix: str = "mt5_error") -> Dict[str, Any]:
        msg = str(e).strip()
        if not msg:
            msg = f"{type(e).__name__}"
        else:
            msg = f"{type(e).__name__}: {msg}"
        return {"ok": False, "error": msg, "where": prefix, "endpoint": self._endpoint()}

    async def connect(self, *, timeout_ms: int = 1500) -> bool:
        self._close()
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=timeout_ms / 1000,
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"MT5 TCP Connection Error: {e}")
            self.connected = False
            self._close()
            return False

    async def _ensure(self) -> bool:
        if not self.connected or self._reader is None or self._writer is None:
            return await self.connect(timeout_ms=1500)
        return True

    def _with_token(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(payload)
        # Bridge requires token; if missing, still send empty (EA will reject with unauthorized)
        out["token"] = self.token
        return out

    async def _send_and_recv_line(self, payload: Dict[str, Any], *, timeout_ms: int) -> str:
        assert self._writer is not None and self._reader is not None

        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self._writer.write(data)
        await self._writer.drain()

        line = await asyncio.wait_for(self._reader.readline(), timeout=timeout_ms / 1000)
        if not line:
            raise ConnectionError("bridge_closed_connection")
        return line.decode("utf-8", errors="replace").strip()

    async def _call(self, payload: Dict[str, Any], *, timeout_ms: int = 2000) -> Dict[str, Any]:
        ok = await self._ensure()
        if not ok:
            return {"ok": False, "error": "mt5_not_connected", "endpoint": self._endpoint()}

        # Single-flight: prevent overlapping requests over the same stream
        async with self._lock:
            try:
                req = self._with_token(payload)
                raw = await self._send_and_recv_line(req, timeout_ms=timeout_ms)

                try:
                    resp = json.loads(raw)
                except Exception:
                    # Keep raw for debugging
                    return {"ok": False, "error": "invalid_json_from_bridge", "raw": raw, "endpoint": self._endpoint()}

                if isinstance(resp, dict):
                    resp.setdefault("endpoint", self._endpoint())
                    return resp

                return {"ok": True, "response": resp, "endpoint": self._endpoint()}
            except Exception as e:
                self.connected = False
                self._close()
                return self._err(e, prefix=f"call:{payload.get('action')}")

    async def ping(self, timeout_ms: int = 800) -> Dict[str, Any]:
        try:
            t0 = time.perf_counter()
            resp = await self._call({"action": "PING"}, timeout_ms=timeout_ms)
            if isinstance(resp, dict) and resp.get("ok") is False:
                # Keep error shape consistent with previous implementation
                raise RuntimeError(str(resp.get("error") or resp.get("message") or "ping_failed"))
            return {
                "ok": True,
                "latency_ms": (time.perf_counter() - t0) * 1000.0,
                "response": resp,
                "endpoint": self._endpoint(),
            }
        except Exception as e:
            out = self._err(e, prefix="ping")
            out["latency_ms"] = 0.0
            return out

    async def account_info(self, *, timeout_ms: int = 2000) -> Dict[str, Any]:
        return await self._call({"action": "ACCOUNT_INFO"}, timeout_ms=timeout_ms)

    async def get_positions(self, *, timeout_ms: int = 2500) -> Dict[str, Any]:
        return await self._call({"action": "GET_POSITIONS"}, timeout_ms=timeout_ms)

    async def get_rates(self, symbol: str, timeframe: str, count: int = 300, *, timeout_ms: int = 3500) -> Dict[str, Any]:
        return await self._call(
            {"action": "RATES", "symbol": symbol, "timeframe": timeframe, "count": int(count)},
            timeout_ms=timeout_ms,
        )

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
            "sl": sl or 0.0,
            "tp": tp or 0.0,
        }
        return await self._call(order, timeout_ms=timeout_ms)


mt5_connector = MT5Connector()
