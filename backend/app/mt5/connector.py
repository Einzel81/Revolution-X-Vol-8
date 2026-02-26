"""MT5 ZMQ Connector.

This project uses a ZMQ REQ/REP bridge. For stability we:
- support ping/health
- support recv timeouts (avoid hanging tasks)
"""

import asyncio
import time
import zmq
import zmq.asyncio

from app.config import settings

class MT5Connector:
    def __init__(self):
        self.context = zmq.asyncio.Context()
        self.socket = None
        self.connected = False
        
    async def connect(self):
        try:
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect(f"tcp://{settings.MT5_HOST}:{settings.MT5_PORT}")
            self.connected = True
            return True
        except Exception as e:
            print(f"MT5 Connection Error: {e}")
            return False

    async def ping(self, timeout_ms: int = 800) -> dict:
        """Best-effort ping.

        Many bridges don't implement PING; fallback to ACCOUNT_INFO.
        """
        if not self.connected:
            await self.connect()

        try:
            t0 = time.perf_counter()
            self.socket.send_json({"action": "PING"})
            resp = await asyncio.wait_for(self.socket.recv_json(), timeout=timeout_ms / 1000)
            return {"ok": True, "latency_ms": (time.perf_counter() - t0) * 1000.0, "response": resp}
        except Exception:
            # fallback
            t0 = time.perf_counter()
            try:
                self.socket.send_json({"action": "ACCOUNT_INFO"})
                resp = await asyncio.wait_for(self.socket.recv_json(), timeout=timeout_ms / 1000)
                return {"ok": True, "latency_ms": (time.perf_counter() - t0) * 1000.0, "response": resp, "fallback": True}
            except Exception as e:
                self.connected = False
                return {"ok": False, "error": str(e)}
    
    async def get_account_info(self):
        if not self.connected:
            await self.connect()
        
        try:
            self.socket.send_json({"action": "ACCOUNT_INFO"})
            response = await self.socket.recv_json()
            return response
        except Exception as e:
            self.connected = False
            return {"error": str(e)}
    
    async def send_order(self, symbol, action, volume, sl, tp, timeout_ms: int = 2000):
        if not self.connected:
            await self.connect()
        
        try:
            order = {
                "action": "SEND_ORDER",
                "symbol": symbol,
                "type": action,  # BUY or SELL
                "volume": volume,
                "sl": sl,
                "tp": tp
            }
            self.socket.send_json(order)
            response = await asyncio.wait_for(self.socket.recv_json(), timeout=timeout_ms / 1000)
            return response
        except Exception as e:
            self.connected = False
            return {"error": str(e)}

mt5_connector = MT5Connector()