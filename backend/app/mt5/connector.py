"""MT5 TCP Bridge connector.

This connector talks to the MQL5 EA bridge over a simple JSON-over-TCP protocol.

Key detail for LIVE deployments:
- The API typically runs inside Docker. If the user configures the MT5 connection
  as 127.0.0.1/localhost (common when using an SSH reverse tunnel that binds on
  the VPS host), then *inside the container* 127.0.0.1 points to the container
  itself, not the VPS host.
- To make this work reliably, we translate localhost/127.0.0.1 to the Docker host
  gateway (or a configured MT5_DOCKER_HOST) when running inside Docker.
"""

from __future__ import annotations

import json
import os
import socket
import time
from typing import Any, Dict, Optional

from app.core.config import settings


class MT5Connector:
    def __init__(self) -> None:
        self.host: str = settings.MT5_HOST
        self.port: int = settings.MT5_PORT
        self.endpoint: str = f"tcp://{self.host}:{self.port}"

        # Shared secret (can be overridden per-connection)
        self.token: str = settings.MT5_BRIDGE_TOKEN or ""

        self.connected: bool = False
        self.last_latency_ms: float = 0.0

    # ----------------------------
    # Helpers
    # ----------------------------
    @staticmethod
    def _is_running_in_docker() -> bool:
        return os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER") == "1"

    def _resolve_host_for_docker(self, host: str) -> str:
        if not settings.MT5_RESOLVE_LOCALHOST_IN_DOCKER:
            return host

        if host not in ("127.0.0.1", "localhost"):
            return host

        if not self._is_running_in_docker():
            return host

        candidate = (settings.MT5_DOCKER_HOST or os.environ.get("MT5_DOCKER_HOST") or "").strip()
        if candidate:
            return candidate

        # Default docker bridge gateway on Linux hosts
        return "172.17.0.1"

    def set_endpoint(self, host: str, port: int) -> None:
        resolved_host = self._resolve_host_for_docker(host)
        self.host = resolved_host
        self.port = int(port)
        self.endpoint = f"tcp://{self.host}:{self.port}"

    def set_token(self, token: Optional[str]) -> None:
        self.token = (token or "").strip()

    # ----------------------------
    # Low-level RPC
    # ----------------------------
    def _rpc(self, payload: Dict[str, Any], timeout: float = 0.8) -> Dict[str, Any]:
        start = time.perf_counter()

        if self.token:
            payload = dict(payload)
            payload["token"] = self.token

        req = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((self.host, self.port))
            s.sendall(req)

            buf = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in buf:
                    buf = buf.split(b"\n", 1)[0]
                    break

            if not buf:
                raise RuntimeError("empty_response")

            resp = json.loads(buf.decode("utf-8", errors="replace"))
            self.connected = True
            return resp if isinstance(resp, dict) else {"ok": True, "data": resp}

        finally:
            try:
                s.close()
            except Exception:
                pass
            self.last_latency_ms = (time.perf_counter() - start) * 1000.0

    # ----------------------------
    # Public API
    # ----------------------------
    def ping(self) -> Dict[str, Any]:
        try:
            resp = self._rpc({"action": "ping"})
            return {
                "ok": True,
                "resp": resp,
                "endpoint": self.endpoint,
                "latency_ms": self.last_latency_ms,
            }
        except Exception as e:
            self.connected = False
            return {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "endpoint": self.endpoint,
                "latency_ms": self.last_latency_ms,
            }

    def get_account(self) -> Dict[str, Any]:
        return self._rpc({"action": "account"})

    def get_positions(self) -> Dict[str, Any]:
        return self._rpc({"action": "positions"})

    def get_orders(self) -> Dict[str, Any]:
        return self._rpc({"action": "orders"})

    def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "",
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "action": "place_order",
            "symbol": symbol,
            "type": order_type,
            "volume": float(volume),
            "comment": comment or "",
        }
        if price is not None:
            payload["price"] = float(price)
        if sl is not None:
            payload["sl"] = float(sl)
        if tp is not None:
            payload["tp"] = float(tp)
        return self._rpc(payload, timeout=2.5)

    def close_position(self, ticket: int) -> Dict[str, Any]:
        return self._rpc({"action": "close_position", "ticket": int(ticket)}, timeout=2.5)

    def close_all(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"action": "close_all"}
        if symbol:
            payload["symbol"] = symbol
        return self._rpc(payload, timeout=5.0)


mt5_connector = MT5Connector()