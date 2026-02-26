from __future__ import annotations

import os
import time
import json
from typing import Dict, Any
import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.training.trainers import load_candles_df, register_model

ARTIFACT_DIR = os.getenv("MODEL_ARTIFACT_DIR", "model_artifacts")


async def train_lstm(db: AsyncSession, symbol: str, timeframe: str) -> Dict[str, Any]:
    """
    Skeleton:
    - loads candles
    - tries to train a simple LSTM if TF available
    - saves artifact
    - registers active model
    """
    df = await load_candles_df(db, symbol, timeframe, limit=8000)
    if len(df) < 1500:
        return {"ok": False, "reason": "not_enough_data"}

    try:
        import numpy as np
        import tensorflow as tf
        from tensorflow.keras import layers, models
    except Exception as e:
        return {"ok": False, "reason": "tensorflow_not_available", "error": str(e)}

    # very simple supervised: predict next return sign
    close = df["close"].astype(float).values
    ret = (pd.Series(close).pct_change().fillna(0.0)).values

    window = 64
    X, y = [], []
    for i in range(window, len(ret) - 1):
        X.append(ret[i-window:i])
        # 3-class: sell/hold/buy
        r = ret[i+1]
        if r > 0.0008:
            y.append(2)  # buy
        elif r < -0.0008:
            y.append(0)  # sell
        else:
            y.append(1)  # hold

    X = np.array(X, dtype="float32")[..., None]  # (n, window, 1)
    y = tf.keras.utils.to_categorical(np.array(y, dtype="int32"), num_classes=3)

    model = models.Sequential([
        layers.Input(shape=(window, 1)),
        layers.LSTM(32),
        layers.Dense(32, activation="relu"),
        layers.Dense(3, activation="softmax")
    ])
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    hist = model.fit(X, y, epochs=3, batch_size=128, verbose=0)

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    path = os.path.join(ARTIFACT_DIR, f"lstm_{symbol}_{timeframe}.keras")
    model.save(path)

    metrics = {
        "samples": int(len(X)),
        "acc": float(hist.history["accuracy"][-1]) if "accuracy" in hist.history else None,
    }
    await register_model(db, "lstm", symbol, timeframe, path, metrics)
    return {"ok": True, "artifact": path, "metrics": metrics}