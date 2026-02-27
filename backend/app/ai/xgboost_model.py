"""
XGBoost Model for Signal Classification
Revolution X - AI System
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class XGBoostPrediction:
    signal: str  # 'buy', 'sell', 'hold'
    probability: float
    feature_importance: Dict[str, float]
    confidence_score: float

class XGBoostModel:
    """
    XGBoost classifier for trading signal prediction
    """
    
    def __init__(self, 
                 n_estimators: int = 200,
                 max_depth: int = 6,
                 learning_rate: float = 0.1):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model = None
        self.feature_names = None
        self.is_trained = False
        
        self._init_model()
    
    def _init_model(self):
        """Initialize XGBoost model"""
        try:
            import xgboost as xgb
            self.model = xgb.XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='mlogloss'
            )
            logger.info("XGBoost model initialized")
        except ImportError:
            logger.warning("XGBoost not available")
            self.model = None
    
    def extract_features(self, df: pd.DataFrame, 
                        smc_data: Optional[Dict] = None,
                        volume_profile: Optional[Dict] = None) -> pd.DataFrame:
        """Extract features for XGBoost"""
        features = pd.DataFrame(index=df.index)
        
        # Price action features
        features['returns'] = df['close'].pct_change()
        features['returns_5'] = df['close'].pct_change(5)
        features['returns_10'] = df['close'].pct_change(10)
        
        # Volatility
        features['volatility'] = features['returns'].rolling(20).std()
        features['atr'] = self._calculate_atr(df)
        
        # Trend features
        features['trend_20'] = (df['close'] > df['close'].rolling(20).mean()).astype(int)
        features['trend_50'] = (df['close'] > df['close'].rolling(50).mean()).astype(int)
        
        # Momentum
        features['rsi'] = self._calculate_rsi(df['close'])
        features['rsi_slope'] = features['rsi'].diff(5)
        
        # MACD
        macd_line, signal_line = self._calculate_macd(df['close'])
        features['macd_histogram'] = macd_line - signal_line
        
        # Volume
        features['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        features['volume_trend'] = (df['volume'] > df['volume'].rolling(20).mean()).astype(int)
        
        # SMC features if available
        if smc_data:
            features['ob_strength'] = smc_data.get('order_block_strength', 0)
            features['fvg_present'] = int(smc_data.get('fair_value_gap', False))
            features['liquidity_sweep'] = int(smc_data.get('liquidity_sweep', False))
        
        # Volume Profile features if available
        if volume_profile:
            features['near_poc'] = int(volume_profile.get('near_poc', False))
            features['in_value_area'] = int(volume_profile.get('in_value_area', False))
            features['volume_concentration'] = volume_profile.get('concentration', 0.5)
        
        # Fill NaN
        features = features.fillna(0)
        
        self.feature_names = features.columns.tolist()
        return features
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        return macd_line, signal_line
    
    def prepare_labels(self, df: pd.DataFrame, forward_period: int = 5) -> pd.Series:
        """Create labels for training"""
        future_returns = df['close'].shift(-forward_period) / df['close'] - 1
        
        labels = pd.Series(index=df.index, dtype='int')
        labels[future_returns > 0.005] = 0  # Buy
        labels[future_returns < -0.005] = 1  # Sell
        labels[(future_returns >= -0.005) & (future_returns <= 0.005)] = 2  # Hold
        
        return labels.fillna(2).astype(int)
    
    def train(self, df: pd.DataFrame, 
              smc_data: Optional[Dict] = None,
              volume_profile: Optional[Dict] = None):
        """Train XGBoost model"""
        if self.model is None:
            logger.error("XGBoost not available")
            return False
        
        features = self.extract_features(df, smc_data, volume_profile)
        labels = self.prepare_labels(df)
        
        # Align lengths
        min_len = min(len(features), len(labels))
        features = features.iloc[:min_len]
        labels = labels.iloc[:min_len]
        
        # Remove NaN
        mask = ~(features.isna().any(axis=1) | labels.isna())
        features = features[mask]
        labels = labels[mask]
        
        self.model.fit(features, labels)
        self.is_trained = True
        
        logger.info("XGBoost training completed")
        return True
    
    def predict(self, df: pd.DataFrame,
                smc_data: Optional[Dict] = None,
                volume_profile: Optional[Dict] = None) -> XGBoostPrediction:
        """Generate prediction"""
        if not self.is_trained or self.model is None:
            # Mock prediction
            return XGBoostPrediction(
                signal='hold',
                probability=0.33,
                feature_importance={},
                confidence_score=0.5
            )
        
        features = self.extract_features(df, smc_data, volume_profile)
        last_features = features.iloc[-1:].values
        
        # Predict probabilities
        proba = self.model.predict_proba(last_features)[0]
        prediction = self.model.predict(last_features)[0]
        
        signals = ['buy', 'sell', 'hold']
        signal = signals[prediction]
        
        # Get feature importance
        importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_.tolist()
        ))
        
        # Sort by importance
        importance = dict(sorted(importance.items(), 
                                key=lambda x: x[1], 
                                reverse=True)[:10])
        
        confidence = proba[prediction]
        
        return XGBoostPrediction(
            signal=signal,
            probability=float(confidence),
            feature_importance=importance,
            confidence_score=float(confidence)
        )
    
    def save(self, path: str):
        """Save model"""
        if self.model:
            import joblib
            joblib.dump(self.model, path)
    
    def load(self, path: str):
        """Load model"""
        try:
            import joblib
            self.model = joblib.load(path)
            self.is_trained = True
        except Exception as e:
            logger.error(f"Failed to load XGBoost model: {e}")
