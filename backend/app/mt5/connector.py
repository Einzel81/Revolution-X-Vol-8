# backend/app/mt5/connector.py
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
    
    async def get_account_info(self):
        if not self.connected:
            await self.connect()
        
        try:
            self.socket.send_json({"action": "ACCOUNT_INFO"})
            response = await self.socket.recv_json()
            return response
        except Exception as e:
            return {"error": str(e)}
    
    async def send_order(self, symbol, action, volume, sl, tp):
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
            response = await self.socket.recv_json()
            return response
        except Exception as e:
            return {"error": str(e)}

mt5_connector = MT5Connector()
