from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import math


def _sma(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / float(len(values))


def _ema(values: List[float], period: int) -> Optional[float]:
    if len(values) < period or period <= 0:
        return None
    k = 2.0 / (period + 1.0)
    ema = values[0]
    for v in values[1:]:
        ema = v * k + ema * (1.0 - k)
    return ema


def _true_range(high: float, low: float, prev_close: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def _atr(data: List[dict], period: int = 14) -> Optional[float]:
    if len(data) < period + 1:
        return None
    trs: List[float] = []
    for i in range(1, len(data)):
        c = data[i]
        p = data[i - 1]
        tr = _true_range(float(c["high"]), float(c["low"]), float(p["close"]))
        trs.append(tr)
    window = trs[-period:]
    return _sma(window)


def _std(values: List[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    mean = sum(values) / float(len(values))
    var = sum((v - mean) ** 2 for v in values) / float(len(values) - 1)
    return math.sqrt(var)


def _bollinger_bandwidth(closes: List[float], period: int = 20, stdev_mult: float = 2.0) -> Optional[float]:
    if len(closes) < period:
        return None
    window = closes[-period:]
    ma = _sma(window)
    sd = _std(window)
    if ma is None or sd is None or ma == 0:
        return None
    upper = ma + stdev_mult * sd
    lower = ma - stdev_mult * sd
    return (upper - lower) / abs(ma)


@dataclass(frozen=True)
class FeatureVector:
    symbol: str
    last_close: float
    atr: Optional[float]
    atr_pct: Optional[float]
    ema_fast: Optional[float]
    ema_slow: Optional[float]
    ema_spread: Optional[float]
    bb_width: Optional[float]
    meta: Dict[str, float]


def build_features(data: List[dict], symbol: str = "XAUUSD") -> FeatureVector:
    """Build a minimal, stable feature vector from raw OHLCV candles."""
    if not data:
        raise ValueError("Empty market data")

    closes = [float(c["close"]) for c in data if "close" in c]
    last_close = closes[-1]

    atr14 = _atr(data, 14)
    atr_pct = (atr14 / last_close) if (atr14 is not None and last_close != 0) else None

    ema_fast = _ema(closes[-60:] if len(closes) > 60 else closes, 20)
    ema_slow = _ema(closes[-120:] if len(closes) > 120 else closes, 50)
    ema_spread = (ema_fast - ema_slow) if (ema_fast is not None and ema_slow is not None) else None

    bb_width = _bollinger_bandwidth(closes, 20, 2.0)

    meta: Dict[str, float] = {
        "n_bars": float(len(data)),
    }
    return FeatureVector(
        symbol=symbol,
        last_close=last_close,
        atr=atr14,
        atr_pct=atr_pct,
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        ema_spread=ema_spread,
        bb_width=bb_width,
        meta=meta,
    ) 