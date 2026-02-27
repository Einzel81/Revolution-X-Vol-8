"""
Ensemble Fusion Engine
Combines LSTM + XGBoost + LightGBM predictions
Revolution X - AI System
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from .lstm_model import LSTMModel, LSTMPrediction
from .xgboost_model import XGBoostModel, XGBoostPrediction
from .lightgbm_model import LightGBMModel, LightGBMPrediction

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

@dataclass
class EnsemblePrediction:
    final_signal: str
    signal_strength: SignalStrength
    confidence: float
    consensus_score: float  # 0-1, how much models agree
    individual_predictions: Dict[str, Dict]
    recommended_action: str
    risk_level: str

class EnsembleFusion:
    """
    Fusion engine that combines predictions from multiple AI models
    """
    
    def __init__(self,
                 lstm_weight: float = 0.35,
                 xgboost_weight: float = 0.40,
                 lightgbm_weight: float = 0.25):
        self.lstm_weight = lstm_weight
        self.xgboost_weight = xgboost_weight
        self.lightgbm_weight = lightgbm_weight
        
        self.lstm = LSTMModel()
        self.xgboost = XGBoostModel()
        self.lightgbm = LightGBMModel()
        
        # Voting thresholds
        self.strong_threshold = 0.75
        self.moderate_threshold = 0.55
        self.min_consensus = 0.6
    
    def normalize_signal(self, signal: str) -> int:
        """Convert signal to numeric"""
        mapping = {
            'buy': 1, 'up': 1,
            'sell': -1, 'down': -1,
            'hold': 0, 'neutral': 0
        }
        return mapping.get(signal.lower(), 0)
    
    def calculate_consensus(self, predictions: List[str]) -> float:
        """Calculate agreement between models"""
        if len(predictions) < 2:
            return 1.0
        
        numeric = [self.normalize_signal(p) for p in predictions]
        
        # Check if all same direction
        if len(set(numeric)) == 1:
            return 1.0
        
        # Check if two agree
        from collections import Counter
        counts = Counter(numeric)
        most_common = counts.most_common(1)[0][1]
        
        return most_common / len(predictions)
    
    def fuse_predictions(self,
                        lstm_pred: LSTMPrediction,
                        xgb_pred: XGBoostPrediction,
                        lgb_pred: LightGBMPrediction) -> EnsemblePrediction:
        """Combine all predictions using weighted voting"""
        
        # Normalize all to buy/sell/hold
        signals = {
            'lstm': lstm_pred.direction,
            'xgboost': xgb_pred.signal,
            'lightgbm': lgb_pred.signal
        }
        
        # Weighted vote
        vote_score = 0
        total_confidence = 0
        
        # LSTM contribution
        lstm_signal = self.normalize_signal(signals['lstm'])
        vote_score += lstm_signal * self.lstm_weight * lstm_pred.confidence
        total_confidence += lstm_pred.confidence * self.lstm_weight
        
        # XGBoost contribution
        xgb_signal = self.normalize_signal(signals['xgboost'])
        vote_score += xgb_signal * self.xgboost_weight * xgb_pred.probability
        total_confidence += xgb_pred.probability * self.xgboost_weight
        
        # LightGBM contribution
        lgb_signal = self.normalize_signal(signals['lightgbm'])
        vote_score += lgb_signal * self.lightgbm_weight * lgb_pred.probability
        total_confidence += lgb_pred.probability * self.lightgbm_weight
        
        # Normalize
        if total_confidence > 0:
            vote_score /= total_confidence
        
        # Determine final signal
        if vote_score > 0.3:
            final_signal = "buy"
        elif vote_score < -0.3:
            final_signal = "sell"
        else:
            final_signal = "hold"
        
        # Calculate consensus
        consensus = self.calculate_consensus(list(signals.values()))
        
        # Determine strength
        abs_score = abs(vote_score)
        if abs_score > 0.7 and consensus > 0.8:
            strength = SignalStrength.STRONG_BUY if vote_score > 0 else SignalStrength.STRONG_SELL
        elif abs_score > 0.5 and consensus > 0.6:
            strength = SignalStrength.BUY if vote_score > 0 else SignalStrength.SELL
        else:
            strength = SignalStrength.NEUTRAL
        
        # Overall confidence
        confidence = (abs_score + consensus) / 2
        
        # Recommended action
        action_map = {
            SignalStrength.STRONG_BUY: "Enter Long Position Immediately",
            SignalStrength.BUY: "Consider Long Position",
            SignalStrength.NEUTRAL: "Wait for Clearer Signal",
            SignalStrength.SELL: "Consider Short Position",
            SignalStrength.STRONG_SELL: "Enter Short Position Immediately"
        }
        
        # Risk assessment
        if consensus < 0.6:
            risk = "high"
        elif confidence < 0.6:
            risk = "medium"
        else:
            risk = "low"
        
        return EnsemblePrediction(
            final_signal=final_signal,
            signal_strength=strength,
            confidence=round(confidence, 3),
            consensus_score=round(consensus, 3),
            individual_predictions={
                'lstm': {
                    'signal': lstm_pred.direction,
                    'confidence': round(lstm_pred.confidence, 3),
                    'predicted_price': round(lstm_pred.predicted_price, 2)
                },
                'xgboost': {
                    'signal': xgb_pred.signal,
                    'probability': round(xgb_pred.probability, 3),
                    'top_features': dict(list(xgb_pred.feature_importance.items())[:3])
                },
                'lightgbm': {
                    'signal': lgb_pred.signal,
                    'probability': round(lgb_pred.probability, 3),
                    'speed_ms': round(lgb_pred.prediction_speed_ms, 2),
                    'agreement': lgb_pred.agreement_with_xgboost
                }
            },
            recommended_action=action_map[strength],
            risk_level=risk
        )
    
    def get_trade_recommendation(self, 
                                  prediction: EnsemblePrediction,
                                  current_price: float,
                                  atr: float) -> Dict:
        """Generate detailed trade recommendation"""
        
        if prediction.signal_strength in [SignalStrength.NEUTRAL]:
            return {
                'action': 'WAIT',
                'reason': 'Insufficient signal strength or consensus',
                'confidence': prediction.confidence
            }
        
        is_buy = prediction.signal_strength in [SignalStrength.BUY, SignalStrength.STRONG_BUY]
        
        # Calculate levels
        stop_loss = current_price - (2 * atr) if is_buy else current_price + (2 * atr)
        take_profit_1 = current_price + (1.5 * atr) if is_buy else current_price - (1.5 * atr)
        take_profit_2 = current_price + (3 * atr) if is_buy else current_price - (3 * atr)
        
        return {
            'action': 'BUY' if is_buy else 'SELL',
            'entry_price': round(current_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit_1': round(take_profit_1, 2),
            'take_profit_2': round(take_profit_2, 2),
            'risk_reward': 1.5 if prediction.signal_strength in [SignalStrength.BUY, SignalStrength.SELL] else 2.0,
            'position_size_suggestion': 'normal' if prediction.confidence > 0.7 else 'reduced',
            'timeframe': 'intraday' if prediction.consensus_score > 0.8 else 'swing'
        }
