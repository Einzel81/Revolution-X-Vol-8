from __future__ import annotations

import httpx
from app.market_data.providers.base import DXYQuote


class TwelveDataDXYProvider:
    name = "twelvedata"

    def __init__(self, api_key: str, symbol: str = "DXY"):
        self.api_key = api_key
        self.symbol = symbol

    async def get_quote(self) -> DXYQuote:
        url = "https://api.twelvedata.com/quote"
        params = {"symbol": self.symbol, "apikey": self.api_key}

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        if data.get("status") == "error":
            raise RuntimeError(f"TwelveData error: {data.get('message')}")

        price = float(data["close"] if "close" in data else data["price"])
        ts = data.get("datetime")
        return DXYQuote(symbol=self.symbol, price=price, timestamp=ts)