"""
DXY-Gold Correlation Analyzer
Revolution X - DXY Guardian
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from scipy import stats
import logging

logger = logging.getLogger(__name__)

@dataclass
class CorrelationAnalysis:
    correlation: float
    r_squared: float
    p_value: float
    beta: float
    alpha: float
    regime: str  # 'strong_inverse', 'moderate_inverse', 'weak', 'positive'
    reliability: str  # 'high', 'medium', 'low'

class DXYCorrelationAnalyzer:
    """
    Analyzes correlation between DXY and Gold (XAUUSD)
    """
    
    def __init__(self, 
                 lookback_periods: Dict[str, int] = None,
                 correlation_threshold: float = -0.6):
        self.lookback_periods = lookback_periods or {
            'short': 20,    # 20 periods
            'medium': 60,   # 60 periods
            'long': 200     # 200 periods
        }
        self.correlation_threshold = correlation_threshold
        self.correlation_history: Dict[str, list] = {
            'short': [], 'medium': [], 'long': []
        }
    
    def calculate_correlation(self, 
                             dxy_data: pd.DataFrame,
                             gold_data: pd.DataFrame,
                             period: str = 'medium') -> CorrelationAnalysis:
        """Calculate correlation for specified period"""
        
        # Align data
        merged = pd.merge(
            dxy_data[['close']].rename(columns={'close': 'dxy'}),
            gold_data[['close']].rename(columns={'close': 'gold'}),
            left_index=True,
            right_index=True,
            how='inner'
        )
        
        if len(merged) < self.lookback_periods[period]:
            return CorrelationAnalysis(
                correlation=0, r_squared=0, p_value=1,
                beta=0, alpha=0, regime='unknown', reliability='low'
            )
        
        # Get lookback window
        window = self.lookback_periods[period]
        data = merged.tail(window)
        
        # Calculate returns
        dxy_returns = data['dxy'].pct_change().dropna()
        gold_returns = data['gold'].pct_change().dropna()
        
        # Ensure same length
        min_len = min(len(dxy_returns), len(gold_returns))
        dxy_returns = dxy_returns.iloc[-min_len:]
        gold_returns = gold_returns.iloc[-min_len:]
        
        # Pearson correlation
        correlation, p_value = stats.pearsonr(dxy_returns, gold_returns)
        
        # Linear regression for beta
        slope, intercept, r_value, _, _ = stats.linregress(dxy_returns, gold_returns)
        
        # Determine regime
        if correlation < -0.8:
            regime = 'strong_inverse'
        elif correlation < -0.5:
            regime = 'moderate_inverse'
        elif correlation < 0:
            regime = 'weak'
        else:
            regime = 'positive'
        
        # Reliability based on p-value
        if p_value < 0.01:
            reliability = 'high'
        elif p_value < 0.05:
            reliability = 'medium'
        else:
            reliability = 'low'
        
        analysis = CorrelationAnalysis(
            correlation=round(correlation, 3),
            r_squared=round(r_value ** 2, 3),
            p_value=round(p_value, 4),
            beta=round(slope, 3),
            alpha=round(intercept, 5),
            regime=regime,
            reliability=reliability
        )
        
        # Store history
        self.correlation_history[period].append({
            'timestamp': pd.Timestamp.now(),
            'correlation': correlation
        })
        
        return analysis
    
    def get_multi_timeframe_correlation(self,
                                         dxy_data: pd.DataFrame,
                                         gold_data: pd.DataFrame) -> Dict[str, CorrelationAnalysis]:
        """Get correlation across all timeframes"""
        results = {}
        
        for period in self.lookback_periods.keys():
            results[period] = self.calculate_correlation(dxy_data, gold_data, period)
        
        return results
    
    def adjust_gold_signal(self,
                          original_signal: str,
                          signal_confidence: float,
                          dxy_impact: Dict,
                          correlation: CorrelationAnalysis) -> Dict:
        """
        Adjust Gold trading signal based on DXY correlation
        """
        adjusted_signal = original_signal
        adjusted_confidence = signal_confidence
        adjustment_reason = []
        
        # Only adjust if correlation is reliable and inverse
        if correlation.reliability in ['high', 'medium'] and correlation.correlation < -0.5:
            
            dxy_trend = dxy_impact.get('impact', 'neutral')
            dxy_strength = dxy_impact.get('strength', 'low')
            
            # DXY bullish = bearish for Gold
            if dxy_trend == 'bullish' and original_signal == 'buy':
                if dxy_strength == 'strong':
                    adjusted_confidence *= 0.5
                    adjustment_reason.append("Strong DXY bullish trend reduces Gold buy confidence")
                else:
                    adjusted_confidence *= 0.8
                    adjustment_reason.append("Moderate DXY strength slightly reduces Gold buy confidence")
            
            # DXY bearish = bullish for Gold
            elif dxy_trend == 'bearish' and original_signal == 'sell':
                if dxy_strength == 'strong':
                    adjusted_confidence *= 0.5
                    adjustment_reason.append("Strong DXY bearish trend reduces Gold sell confidence")
                else:
                    adjusted_confidence *= 0.8
                    adjustment_reason.append("Moderate DXY weakness slightly reduces Gold sell confidence")
            
            # Confirming signals
            elif dxy_trend == 'bearish' and original_signal == 'buy':
                if dxy_strength == 'strong':
                    adjusted_confidence = min(1.0, adjusted_confidence * 1.2)
                    adjustment_reason.append("DXY weakness confirms Gold buy signal")
            
            elif dxy_trend == 'bullish' and original_signal == 'sell':
                if dxy_strength == 'strong':
                    adjusted_confidence = min(1.0, adjusted_confidence * 1.2)
                    adjustment_reason.append("DXY strength confirms Gold sell signal")
        
        else:
            adjustment_reason.append("DXY correlation weak or unreliable, minimal adjustment")
        
        return {
            'original_signal': original_signal,
            'adjusted_signal': adjusted_signal,
            'original_confidence': signal_confidence,
            'adjusted_confidence': round(adjusted_confidence, 3),
            'adjustments': adjustment_reason,
            'correlation_used': correlation.correlation,
            'recommendation': 'proceed' if adjusted_confidence > 0.6 else 'caution'
        }
    
    def get_correlation_trend(self, period: str = 'medium') -> str:
        """Get trend of correlation over time"""
        history = self.correlation_history[period]
        
        if len(history) < 10:
            return 'insufficient_data'
        
        recent = [h['correlation'] for h in history[-10:]]
        older = [h['correlation'] for h in history[-20:-10]] if len(history) >= 20 else recent[:5]
        
        recent_avg = np.mean(recent)
        older_avg = np.mean(older)
        
        diff = recent_avg - older_avg
        
        if diff > 0.1:
            return 'strengthening_inverse' if recent_avg < 0 else 'turning_positive'
        elif diff < -0.1:
            return 'weakening' if recent_avg < 0 else 'strengthening_positive'
        else:
            return 'stable'
    
    def get_trading_insights(self,
                            dxy_data: pd.DataFrame,
                            gold_data: pd.DataFrame) -> Dict:
        """Generate comprehensive trading insights"""
        
        correlations = self.get_multi_timeframe_correlation(dxy_data, gold_data)
        
        # Weight by reliability
        weighted_corr = 0
        total_weight = 0
        
        for period, corr in correlations.items():
            weight = {'short': 0.2, 'medium': 0.5, 'long': 0.3}[period]
            if corr.reliability == 'high':
                weight *= 1.0
            elif corr.reliability == 'medium':
                weight *= 0.7
            else:
                weight *= 0.4
            
            weighted_corr += corr.correlation * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_corr /= total_weight
        
        return {
            'current_correlation': round(weighted_corr, 3),
            'timeframe_analysis': {
                period: {
                    'correlation': corr.correlation,
                    'regime': corr.regime,
                    'reliability': corr.reliability
                }
                for period, corr in correlations.items()
            },
            'correlation_trend': self.get_correlation_trend('medium'),
            'trading_implications': self._generate_implications(weighted_corr),
            'hedging_recommendation': self._hedging_recommendation(correlations['medium'])
        }
    
    def _generate_implications(self, correlation: float) -> List[str]:
        """Generate trading implications"""
        implications = []
        
        if correlation < -0.8:
            implications.append("Strong inverse correlation - DXY is excellent Gold predictor")
            implications.append("Consider DXY as leading indicator for Gold entries")
        elif correlation < -0.5:
            implications.append("Moderate inverse correlation - DXY useful for confirmation")
            implications.append("Combine DXY analysis with other signals")
        elif correlation < 0:
            implications.append("Weak inverse correlation - DXY has limited predictive power")
            implications.append("Rely more on technical analysis")
        else:
            implications.append("Positive correlation detected - unusual regime")
            implications.append("Check for market stress or safe-haven flows")
        
        return implications
    
    def _hedging_recommendation(self, correlation: CorrelationAnalysis) -> str:
        """Generate hedging recommendation"""
        if correlation.correlation < -0.7 and correlation.reliability == 'high':
            return "Strong hedge potential: Long Gold + Short DXY (or USD pairs)"
        elif correlation.correlation < -0.5:
            return "Moderate hedge: Monitor DXY for Gold reversal signals"
        else:
            return "Weak correlation: DXY not reliable for Gold hedging"
