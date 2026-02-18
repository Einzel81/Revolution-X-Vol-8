"""
LightGBM Model for Signal Confirmation
Revolution X - AI System
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LightGBMPrediction:
    signal: str
    probability: float
    prediction_speed_ms: float
    agreement_with_xgboost: bool

class LightGBMModel:
    """
    LightGBM classifier for fast signal confirmation
    """
    
    def __init__(self,
                 n_estimators: int = 150,
                 num_leaves: int = 31,
                 learning_rate: float = 0.1):
        self.n_estimators = n_estimators
        self.num_leaves = num_leaves
        self.learning_rate = learning_rate
        self.model = None
        self.is_trained = False
        
        self._init_model()
    
    def _init_model(self):
        """Initialize LightGBM"""
        try:
            import lightgbm as lgb
            self.model = lgb.LGBMClassifier(
                n_estimators=self.n_estimators,
                num_leaves=self.num_leaves,
                learning_rate=self.learning_rate,
                feature_fraction=0.8,
                bagging_fraction=0.8,
                bagging_freq=5,
                verbose=-1
            )
            logger.info("LightGBM model initialized")
        except ImportError:
            logger.warning("LightGBM not available")
            self.model = None
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract optimized features for LightGBM"""
        features = pd.DataFrame()
        
        # Fast calculation features
        features['price_momentum'] = df['close'].pct_change(3)
        features['volume_surge'] = df['volume'] / df['volume'].rolling(10).mean()
        
        # Short-term trends
        for period in [5, 10, 15]:
            ma = df['close'].rolling(period).mean()
            features[f'dist_from_ma_{period}'] = (df['close'] - ma) / ma
        
        # Price patterns
        features['body_size'] = (df['close'] - df['open']) / (df['high'] - df['low'] + 0.001)
        features['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / (df['high'] - df['low'] + 0.001)
        features['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / (df['high'] - df['low'] + 0.001)
        
        # Volatility regime
        features['volatility_regime'] = df['close'].pct_change().rolling(10).std() / \
                                       df['close'].pct_change().rolling(30).std()
        
        # Mean reversion signals
        features['distance_from_high'] = (df['high'].rolling(20).max() - df['close']) / df['close']
        features['distance_from_low'] = (df['close'] - df['low'].rolling(20).min()) / df['close']
        
        return features.fillna(0)
    
    def prepare_labels(self, df: pd.DataFrame) -> pd.Series:
        """Create labels"""
        future_return = df['close'].shift(-3) / df['close'] - 1
        
        labels = pd.Series(2, index=df.index)  # Default hold
        labels[future_return > 0.003] = 0  # Buy
        labels[future_return < -0.003] = 1  # Sell
        
        return labels
    
    def train(self, df: pd.DataFrame):
        """Train LightGBM"""
        if self.model is None:
            return False
        
        import time
        start = time.time()
        
        features = self.extract_features(df)
        labels = self.prepare_labels(df)
        
        # Align and clean
        min_len = min(len(features), len(labels))
        features = features.iloc[:min_len]
        labels = labels.iloc[:min_len]
        
        mask = ~(features.isna().any(axis=1))
        features = features[mask]
        labels = labels[mask]
        
        self.model.fit(features, labels)
        self.is_trained = True
        
        train_time = time.time() - start
        logger.info(f"LightGBM trained in {train_time:.2f}s")
        return True
    
    def predict(self, df: pd.DataFrame, 
                xgboost_signal: Optional[str] = None) -> LightGBMPrediction:
        """Generate fast prediction"""
        import time
        
        if not self.is_trained or self.model is None:
            return LightGBMPrediction(
                signal='hold',
                probability=0.33,
                prediction_speed_ms=0,
                agreement_with_xgboost=True
            )
        
        start = time.time()
        
        features = self.extract_features(df)
        last_features = features.iloc[-1:].values
        
        proba = self.model.predict_proba(last_features)[0]
        prediction = self.model.predict(last_features)[0]
        
        signals = ['buy', 'sell', 'hold']
        signal = signals[prediction]
        
        speed = (time.time() - start) * 1000
        
        agreement = True
        if xgboost_signal:
            agreement = (signal == xgboost_signal)
        
        return LightGBMPrediction(
            signal=signal,
            probability=float(proba[prediction]),
            prediction_speed_ms=speed,
            agreement_with_xgboost=agreement
        )
    
    def save(self, path: str):
        """Save model"""
        if self.model:
            self.model.booster_.save_model(path)
    
    def load(self, path: str):
        """Load model"""
        try:
            import lightgbm as lgb
            self.model = lgb.Booster(model_file=path)
            self.is_trained = True
        except Exception as e:
            logger.error(f"Failed to load LightGBM: {e}")
