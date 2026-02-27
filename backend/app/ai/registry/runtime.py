# backend/app/ai/registry/runtime.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import time
import os

import joblib
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.model_registry import ModelRegistry


@dataclass(frozen=True)
class RegistryPrediction:
    direction: str           # bullish|bearish|neutral
    prob: float              # 0..1
    probs: Dict[str, float]  # buy/sell/hold
    used_models: Dict[str, str]  # model_type -> version
    notes: list[str]


class ModelCache:
    def __init__(self):
        self.loaded: Dict[str, Dict[str, Any]] = {}  # key -> artifact data
        self.last_refresh: float = 0.0
        self.refresh_ttl: float = 30.0  # seconds

    def _key(self, model_type: str, symbol: str, timeframe: str) -> str:
        return f"{model_type}:{symbol}:{timeframe}"

    async def get_active(self, db: AsyncSession, model_type: str, symbol: str, timeframe: str) -> Optional[ModelRegistry]:
        q = select(ModelRegistry).where(
            (ModelRegistry.model_type == model_type) &
            (ModelRegistry.symbol == symbol) &
            (ModelRegistry.timeframe == timeframe) &
            (ModelRegistry.is_active == True)
        )
        row = await db.execute(q)
        return row.scalar_one_or_none()

    def load_artifact(self, artifact_path: str) -> Optional[Dict[str, Any]]:
        if not artifact_path or not os.path.exists(artifact_path):
            return None
        return joblib.load(artifact_path)

    async def get_model_artifact(
        self,
        db: AsyncSession,
        model_type: str,
        symbol: str,
        timeframe: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[ModelRegistry]]:
        reg = await self.get_active(db, model_type, symbol, timeframe)
        if not reg:
            return None, None

        key = self._key(model_type, symbol, timeframe)
        cached = self.loaded.get(key)

        # reload only if artifact path changed
        if cached and cached.get("_artifact_path") == reg.artifact_path and cached.get("_version") == reg.version:
            return cached, reg

        artifact = self.load_artifact(reg.artifact_path)
        if artifact is None:
            return None, reg

        artifact["_artifact_path"] = reg.artifact_path
        artifact["_version"] = reg.version
        self.loaded[key] = artifact
        return artifact, reg


_cache = ModelCache()


def _feature_row_from_vector(feature_vector: Any, feature_names: list[str]) -> np.ndarray:
    """
    Map FeatureVector -> ndarray aligned to trained feature_names.
    Missing features -> 0.0 (safe).
    """
    d = {}
    # Works with dataclass-like objects (FeatureVector) or dict
    if isinstance(feature_vector, dict):
        d = feature_vector
    else:
        # generic: read attributes
        for name in feature_names:
            if hasattr(feature_vector, name):
                try:
                    d[name] = float(getattr(feature_vector, name))
                except Exception:
                    d[name] = 0.0

    x = []
    for name in feature_names:
        v = d.get(name, 0.0)
        try:
            x.append(float(v))
        except Exception:
            x.append(0.0)
    return np.array([x], dtype=float)


def _probs_to_direction(probs: Dict[str, float]) -> Tuple[str, float]:
    # buy/sell/hold probs expected
    buy = float(probs.get("buy", 0.0))
    sell = float(probs.get("sell", 0.0))
    hold = float(probs.get("hold", 0.0))

    best = max(buy, sell, hold)
    if best == hold or abs(buy - sell) < 0.05:
        return "neutral", max(hold, 0.5)

    if buy > sell:
        return "bullish", buy
    return "bearish", sell


async def predict_from_registry(
    db: Optional[AsyncSession],
    symbol: str,
    timeframe: str,
    feature_vector: Any,
) -> Optional[RegistryPrediction]:
    """
    Uses active XGB + LGBM models if present.
    Returns None if DB not provided or no models available.
    """
    if db is None:
        return None

    notes: list[str] = []
    used: Dict[str, str] = {}
    probs_acc = {"buy": 0.0, "hold": 0.0, "sell": 0.0}
    n = 0

    # XGBoost (multiclass: 0 sell, 1 hold, 2 buy)
    art, reg = await _cache.get_model_artifact(db, "xgboost", symbol, timeframe)
    if art and reg:
        model = art.get("model")
        feature_names = art.get("feature_names") or []
        if model is not None and feature_names:
            x = _feature_row_from_vector(feature_vector, feature_names)
            p = model.predict_proba(x)[0]
            # map
            probs_acc["sell"] += float(p[0])
            probs_acc["hold"] += float(p[1])
            probs_acc["buy"] += float(p[2])
            used["xgboost"] = reg.version
            n += 1
        else:
            notes.append("xgboost artifact missing model/features")

    # LightGBM (same mapping)
    art, reg = await _cache.get_model_artifact(db, "lightgbm", symbol, timeframe)
    if art and reg:
        model = art.get("model")
        feature_names = art.get("feature_names") or []
        if model is not None and feature_names:
            x = _feature_row_from_vector(feature_vector, feature_names)
            p = model.predict_proba(x)[0]
            probs_acc["sell"] += float(p[0])
            probs_acc["hold"] += float(p[1])
            probs_acc["buy"] += float(p[2])
            used["lightgbm"] = reg.version
            n += 1
        else:
            notes.append("lightgbm artifact missing model/features")

    if n == 0:
        return None

    probs = {k: v / n for k, v in probs_acc.items()}
    direction, prob = _probs_to_direction(probs)

    return RegistryPrediction(
        direction=direction,
        prob=float(prob),
        probs=probs,
        used_models=used,
        notes=notes + ["registry_models_used"],
    )