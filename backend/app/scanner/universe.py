import json
from typing import List, Dict, Any, Tuple

DEFAULT_UNIVERSE = {
    "symbols": [
        {"symbol": "XAUUSD", "weight": 1.0},   # gold priority
        {"symbol": "XAGUSD", "weight": 0.7},   # silver
        {"symbol": "XPTUSD", "weight": 0.4},   # platinum
        {"symbol": "XPDUSD", "weight": 0.4},   # palladium
        {"symbol": "EURUSD", "weight": 0.3},
        {"symbol": "USDJPY", "weight": 0.3},
    ],
    "timeframes": ["M5", "M15", "H1"],
    "min_candles": 200,
    "top_k": 10
}

def parse_universe(raw: str | None) -> Dict[str, Any]:
    if not raw:
        return DEFAULT_UNIVERSE
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return DEFAULT_UNIVERSE
        return {**DEFAULT_UNIVERSE, **data}
    except Exception:
        return DEFAULT_UNIVERSE

def rank_score(base_score: float, symbol_weight: float) -> float:
    return float(base_score) * float(symbol_weight)