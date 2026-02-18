"""
LSTM Neural Network for Time Series Forecasting
Revolution X - AI System
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LSTMPrediction:
    direction: str  # 'up', 'down', 'neutral'
    confidence: float
    predicted_price: float
    sequence_probabilities: List[float]

class LSTMModel:
    """
    LSTM Neural Network for price prediction and pattern recognition
    """
    
    def __init__(self, 
                 sequence_length: int = 60,
                 n_features: int = 20,
                 model_path: Optional[str] = None):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        self._build_model()
    
    def _build_model(self):
        """Build LSTM architecture"""
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
            
            self.model = Sequential([
                LSTM(128, return_sequences=True, 
                     input_shape=(self.sequence_length, self.n_features)),
                BatchNormalization(),
                Dropout(0.2),
                
                LSTM(64, return_sequences=True),
                BatchNormalization(),
                Dropout(0.2),
                
                LSTM(32, return_sequences=False),
                BatchNormalization(),
                Dropout(0.2),
                
                Dense(16, activation='relu'),
                Dense(3, activation='softmax')  # up, down, neutral
            ])
            
            self.model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            logger.info("LSTM model built successfully")
            
        except ImportError:
            logger.warning("TensorFlow not available, using mock LSTM")
            self.model = None
    
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare technical features for LSTM"""
        features = pd.DataFrame()
        
        # Price features
        features['returns'] = df['close'].pct_change()
        features['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            features[f'ma_{period}'] = df['close'].rolling(period).mean()
            features[f'ma_ratio_{period}'] = df['close'] / features[f'ma_{period}']
        
        # Volatility
        features['volatility'] = features['returns'].rolling(20).std()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        bb_middle = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        features['bb_position'] = (df['close'] - bb_middle) / (2 * bb_std)
        
        # Volume features
        features['volume_ma'] = df['volume'].rolling(20).mean()
        features['volume_ratio'] = df['volume'] / features['volume_ma']
        
        # Price position
        features['high_low_range'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        features = features.fillna(method='ffill').fillna(0)
        
        return features.values
    
    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:(i + self.sequence_length)])
            
            # Label based on future returns
            future_return = data[i + self.sequence_length][0]  # returns column
            if future_return > 0.001:
                y.append([1, 0, 0])  # up
            elif future_return < -0.001:
                y.append([0, 1, 0])  # down
            else:
                y.append([0, 0, 1])  # neutral
        
        return np.array(X), np.array(y)
    
    def train(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 32):
        """Train LSTM model"""
        if self.model is None:
            logger.error("Model not initialized")
            return False
        
        features = self.prepare_features(df)
        X, y = self.create_sequences(features)
        
        # Split train/validation
        split = int(0.8 * len(X))
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )
        
        self.is_trained = True
        logger.info("LSTM training completed")
        return True
    
    def predict(self, df: pd.DataFrame) -> LSTMPrediction:
        """Generate prediction"""
        if not self.is_trained or self.model is None:
            # Return mock prediction for demo
            return LSTMPrediction(
                direction='neutral',
                confidence=0.5,
                predicted_price=df['close'].iloc[-1],
                sequence_probabilities=[0.33, 0.33, 0.34]
            )
        
        features = self.prepare_features(df)
        last_sequence = features[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        
        prediction = self.model.predict(last_sequence, verbose=0)[0]
        
        directions = ['up', 'down', 'neutral']
        direction_idx = np.argmax(prediction)
        
        return LSTMPrediction(
            direction=directions[direction_idx],
            confidence=float(prediction[direction_idx]),
            predicted_price=df['close'].iloc[-1] * (1 + prediction[0] * 0.01),
            sequence_probabilities=prediction.tolist()
        )
    
    def save(self, path: str):
        """Save model"""
        if self.model:
            self.model.save(path)
    
    def load(self, path: str):
        """Load model"""
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(path)
            self.is_trained = True
        except Exception as e:
            logger.error(f"Failed to load LSTM model: {e}")
