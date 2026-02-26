from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class DXYQuote:
    symbol: str
    price: float
    timestamp: Optional[str] = None


class DXYProvider(Protocol):
    name: str
    async def get_quote(self) -> DXYQuote:
        ...