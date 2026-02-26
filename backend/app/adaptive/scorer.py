from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.adaptive.regimes import MarketRegime, RegimeType, clamp01


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    components: Dict[str, float]
    reasons: List[str]


def _apply_weights(components: Dict[str, float], weights: Optional[Dict[str, float]]) -> Dict[str, float]:
    if not weights:
        return components
    out: Dict[str, float] = {}
    for k, v in components.items():
        w = float(weights.get(k, 1.0))
        out[k] = float(v) * w
    return out


def score_signal(
    *,
    base_confidence: float,  # 0..1
    regime: MarketRegime,
    supported_regimes: Optional[List[RegimeType]],
    killzone_can_trade: bool,
    spread_ok: bool = True,
    dxy_ok: bool = True,
    rr_ok: bool = True,
    # Optional per-regime weights: {"confidence":1.0,"killzone":1.0,"dxy":1.0,...}
    regime_weights: Optional[Dict[str, float]] = None,
) -> ScoreBreakdown:
    """Convert a candidate signal into a comparable score (0..100-ish)."""
    components: Dict[str, float] = {}
    reasons: List[str] = []

    c = clamp01(base_confidence)
    components["confidence"] = 60.0 * c

    # Regime match bonus/penalty
    if supported_regimes:
        if regime.primary in supported_regimes:
            components["regime_match"] = 15.0
        else:
            components["regime_mismatch"] = -20.0
            reasons.append(f"Regime mismatch: {regime.primary.value}")
    else:
        components["regime_unknown"] = 0.0

    # Kill zone gate
    if killzone_can_trade:
        components["killzone"] = 10.0
    else:
        components["killzone"] = -50.0
        reasons.append("Outside optimal trading hours")

    if not spread_ok:
        components["spread"] = -15.0
        reasons.append("Spread/liquidity not acceptable")

    if not dxy_ok:
        components["dxy"] = -12.0
        reasons.append("DXY context adverse")

    if not rr_ok:
        components["rr"] = -10.0
        reasons.append("Risk/Reward not acceptable")

    weighted = _apply_weights(components, regime_weights)
    total = sum(weighted.values())
    return ScoreBreakdown(total=total, components=weighted, reasons=reasons)