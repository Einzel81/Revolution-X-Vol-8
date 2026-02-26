from __future__ import annotations

import httpx
from typing import Optional

from app.market_data.providers.base import DXYQuote


class YahooDXYProvider:
    name = "yahoo"

    def __init__(self, symbol: str = "DX-Y.NYB"):
        self.symbol = symbol

    async def get_quote(self) -> DXYQuote:
        # Unofficial but works for MVP
        url = "https://query1.finance.yahoo.com/v7/finance/quote"
        params = {"symbols": self.symbol}

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        result = (data.get("quoteResponse") or {}).get("result") or []
        if not result:
            raise RuntimeError("Yahoo: Empty quoteResponse")

        item = result[0]
        price = float(item.get("regularMarketPrice"))
        ts = item.get("regularMarketTime")
        return DXYQuote(symbol=self.symbol, price=price, timestamp=str(ts) if ts is not None else None)