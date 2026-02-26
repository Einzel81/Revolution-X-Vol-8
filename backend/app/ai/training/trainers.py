import os
import json
import time
import joblib
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.candle import Candle
from app.models.model_registry import ModelRegistry
from app.models.model_training_run import ModelTrainingRun
from app.ai.xgboost_model import XGBoostModel
from app.ai.lightgbm_model import LightGBMModel
from app.ai.training.dataset import build_labels, to_multiclass

ARTIFACT_DIR = os.getenv("MODEL_ARTIFACT_DIR", "model_artifacts")

async def load_candles_df(db: AsyncSession, symbol: str, timeframe: str, limit: int = 5000) -> pd.DataFrame:
    q = (
        select(Candle)
        .where((Candle.symbol == symbol) & (Candle.timeframe == timeframe))
        .order_by(desc(Candle.time))
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    rows = list(reversed(rows))
    df = pd.DataFrame([{
        "time": r.time, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume
    } for r in rows])
    return df

async def register_model(db: AsyncSession, model_type: str, symbol: str, timeframe: str, artifact_path: str, metrics: dict) -> None:
    # deactivate previous active
    rows = (await db.execute(select(ModelRegistry).where(
        (ModelRegistry.model_type == model_type) &
        (ModelRegistry.symbol == symbol) &
        (ModelRegistry.timeframe == timeframe) &
        (ModelRegistry.is_active == True)
    ))).scalars().all()
    for r in rows:
        r.is_active = False

    version = str(int(time.time()))
    reg = ModelRegistry(
        model_type=model_type,
        symbol=symbol,
        timeframe=timeframe,
        version=version,
        artifact_path=artifact_path,
        metrics=metrics,
        is_active=True
    )
    db.add(reg)
    await db.commit()

async def train_xgb(db: AsyncSession, symbol: str, timeframe: str) -> dict:
    df = await load_candles_df(db, symbol, timeframe)
    if len(df) < 800:
        return {"ok": False, "reason": "not_enough_data"}

    model = XGBoostModel()
    X = model.extract_features(df).dropna()
    y = build_labels(df.loc[X.index]).loc[X.index]
    y_mc = to_multiclass(y)

    model.model.fit(X.values, y_mc)
    model.is_trained = True

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    path = os.path.join(ARTIFACT_DIR, f"xgb_{symbol}_{timeframe}.joblib")
    joblib.dump({"model": model.model, "feature_names": list(X.columns)}, path)

    metrics = {"samples": int(len(X))}
    await register_model(db, "xgboost", symbol, timeframe, path, metrics)
    return {"ok": True, "artifact": path, "metrics": metrics}

async def train_lgbm(db: AsyncSession, symbol: str, timeframe: str) -> dict:
    df = await load_candles_df(db, symbol, timeframe)
    if len(df) < 800:
        return {"ok": False, "reason": "not_enough_data"}

    model = LightGBMModel()
    X = model.extract_features(df).dropna()
    y = build_labels(df.loc[X.index]).loc[X.index]
    y_mc = to_multiclass(y)

    model.model.fit(X.values, y_mc)
    model.is_trained = True

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    path = os.path.join(ARTIFACT_DIR, f"lgbm_{symbol}_{timeframe}.joblib")
    joblib.dump({"model": model.model, "feature_names": list(X.columns)}, path)

    metrics = {"samples": int(len(X))}
    await register_model(db, "lightgbm", symbol, timeframe, path, metrics)
    return {"ok": True, "artifact": path, "metrics": metrics}