from __future__ import annotations

from typing import List, Optional, Tuple
import math


def _pct_returns(series: List[float]) -> List[float]:
    r: List[float] = []
    for i in range(1, len(series)):
        a, b = series[i - 1], series[i]
        if a == 0:
            continue
        r.append((b - a) / a)
    return r


def rolling_corr(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) < 5 or len(y) < 5:
        return None
    if len(x) != len(y):
        n = min(len(x), len(y))
        x, y = x[-n:], y[-n:]

    xr = _pct_returns(x)
    yr = _pct_returns(y)
    n = min(len(xr), len(yr))
    if n < 5:
        return None
    xr, yr = xr[-n:], yr[-n:]

    mx = sum(xr) / n
    my = sum(yr) / n
    cov = sum((xr[i] - mx) * (yr[i] - my) for i in range(n))
    vx = sum((xr[i] - mx) ** 2 for i in range(n))
    vy = sum((yr[i] - my) ** 2 for i in range(n))
    if vx <= 0 or vy <= 0:
        return None
    return cov / math.sqrt(vx * vy)


def corr_strength(c: Optional[float]) -> Tuple[Optional[float], str]:
    if c is None:
        return None, "low"
    ac = abs(c)
    if ac >= 0.65:
        return c, "strong"
    if ac >= 0.35:
        return c, "moderate"
    return c, "low"