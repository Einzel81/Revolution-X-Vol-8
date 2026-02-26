from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class RegimeType(str, Enum):
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    HIGH_VOLATILITY = "high_volatility"
    LOW_LIQUIDITY = "low_liquidity"


@dataclass(frozen=True)
class MarketRegime:
    primary: RegimeType
    tags: Dict[str, bool]
    confidence: float  # 0..1
    reasons: Dict[str, float]  # metric -> value

    def is_trend(self) -> bool:
        return self.primary in (RegimeType.TREND_UP, RegimeType.TREND_DOWN)

    def is_range(self) -> bool:
        return self.primary == RegimeType.RANGE


def clamp01(x: float) -> float:
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return float(x) 