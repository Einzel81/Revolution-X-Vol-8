from __future__ import annotations

import httpx
from app.market_data.providers.base import DXYQuote


class FMPDXYProvider:
    name = "fmp"

    def __init__(self, api_key: str, symbol: str = "DXY"):
        self.api_key = api_key
        self.symbol = symbol

    async def get_quote(self) -> DXYQuote:
        # FMP index quote endpoint
        url = "https://financialmodelingprep.com/api/v3/quote"
        params = {"symbol": self.symbol, "apikey": self.api_key}

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        # Usually list response
        if isinstance(data, list) and data:
            item = data[0]
            price = float(item["price"])
            ts = item.get("timestamp")
            return DXYQuote(symbol=self.symbol, price=price, timestamp=str(ts) if ts is not None else None)

        raise RuntimeError("FMP: Empty quote response")