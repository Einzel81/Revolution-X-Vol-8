from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import math


@dataclass(frozen=True)
class AIPrediction:
    direction: str  # "bullish"|"bearish"|"neutral"
    prob: float     # 0..1 confidence in direction
    model_votes: Dict[str, float]  # model->prob bullish (or signed score)
    risk_flag: bool
    notes: List[str]


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else (1.0 if x > 1.0 else float(x))


class AIEnsemblePredictor:
    """
    MVP production-safe:
    - If models exist: use them
    - If not: fallback to heuristic probability using price action features passed in
    """
    def __init__(self):
        # placeholders for later real model loading
        self.loaded = False
        self.models: Dict[str, Any] = {}

    def predict(self, features: Dict[str, Any]) -> AIPrediction:
        notes: List[str] = []
        votes: Dict[str, float] = {}

        # If real models are not loaded, fallback:
        # heuristic: use ema_spread + bb_width + atr_pct if present
        ema_spread = features.get("ema_spread")
        atr_pct = features.get("atr_pct")
        bb_width = features.get("bb_width")

        score = 0.0
        if isinstance(ema_spread, (int, float)):
            score += math.tanh(float(ema_spread) * 1000.0)
        if isinstance(bb_width, (int, float)):
            score -= math.tanh((float(bb_width) - 0.012) * 30.0) * 0.3
        if isinstance(atr_pct, (int, float)):
            # very high vol => reduce confidence
            score *= (0.9 if float(atr_pct) > 0.006 else 1.0)

        # convert score -> prob
        prob_bull = clamp01(0.5 + 0.25 * score)
        prob_bear = 1.0 - prob_bull

        # direction
        if abs(prob_bull - 0.5) < 0.05:
            direction = "neutral"
            prob = 0.5
        elif prob_bull > 0.5:
            direction = "bullish"
            prob = prob_bull
        else:
            direction = "bearish"
            prob = prob_bear

        votes["fallback"] = prob_bull
        risk_flag = bool(isinstance(atr_pct, (int, float)) and float(atr_pct) > 0.008)

        notes.append("AI fallback heuristic (models not loaded)")
        if risk_flag:
            notes.append("AI risk_flag: very high volatility")

        return AIPrediction(direction=direction, prob=prob, model_votes=votes, risk_flag=risk_flag, notes=notes)