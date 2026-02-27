import pandas as pd
import numpy as np
from typing import Tuple

def build_labels(df: pd.DataFrame, horizon: int = 5, thr: float = 0.0015) -> pd.Series:
    # label based on forward return
    fwd = df["close"].shift(-horizon) / df["close"] - 1.0
    y = pd.Series(0, index=df.index)  # 0 hold
    y[fwd > thr] = 1   # buy
    y[fwd < -thr] = -1 # sell
    return y

def to_multiclass(y: pd.Series) -> np.ndarray:
    # map -1,0,1 -> 0,1,2
    return y.map({-1:0, 0:1, 1:2}).astype(int).values