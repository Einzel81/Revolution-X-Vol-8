# backend/app/strategies/price_action.py
"""
Price Action Analysis
- Candlestick Patterns
- Support/Resistance Levels
- Trend Analysis
"""

from dataclasses import dataclass
from typing import List, Optional, Literal
from enum import Enum
import numpy as np

class CandlePattern(Enum):
    DOJI = "doji"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"

@dataclass
class Pattern:
    type: CandlePattern
    strength: str  # weak, moderate, strong
    timestamp: str
    price: float

@dataclass
class SupportResistance:
    level: float
    type: Literal["support", "resistance"]
    strength: int  # number of touches
    last_touch: str

class PriceActionAnalyzer:
    def __init__(self, data: List[dict]):
        self.data = data
        self.patterns: List[Pattern] = []
        self.levels: List[SupportResistance] = []
        
    def analyze(self) -> dict:
        """Run full Price Action analysis"""
        self.detect_patterns()
        self.find_support_resistance()
        self.analyze_trend()
        
        return {
            "patterns": self.patterns,
            "support_resistance": self.levels,
            "trend": self.trend
        }
    
    def detect_patterns(self) -> List[Pattern]:
        """Detect candlestick patterns"""
        self.patterns = []
        
        if len(self.data) < 3:
            return self.patterns
        
        for i in range(2, len(self.data)):
            candle = self.data[i]
            prev = self.data[i - 1]
            prev2 = self.data[i - 2]
            
            # Single candle patterns
            if self._is_doji(candle):
                self.patterns.append(Pattern(
                    type=CandlePattern.DOJI,
                    strength="weak",
                    timestamp=candle['timestamp'],
                    price=candle['close']
                ))
            
            if self._is_hammer(candle):
                self.patterns.append(Pattern(
                    type=CandlePattern.HAMMER,
                    strength="moderate",
                    timestamp=candle['timestamp'],
                    price=candle['close']
                ))
            
            if self._is_shooting_star(candle):
                self.patterns.append(Pattern(
                    type=CandlePattern.SHOOTING_STAR,
                    strength="moderate",
                    timestamp=candle['timestamp'],
                    price=candle['close']
                ))
            
            # Two candle patterns
            if self._is_engulfing_bullish(prev, candle):
                strength = "strong" if candle['volume'] > prev['volume'] * 1.5 else "moderate"
                self.patterns.append(Pattern(
                    type=CandlePattern.ENGULFING_BULLISH,
                    strength=strength,
                    timestamp=candle['timestamp'],
                    price=candle['close']
                ))
            
            if self._is_engulfing_bearish(prev, candle):
                strength = "strong" if candle['volume'] > prev['volume'] * 1.5 else "moderate"
                self.patterns.append(Pattern(
                    type=CandlePattern.ENGULFING_BEARISH,
                    strength=strength,
                    timestamp=candle['timestamp'],
                    price=candle['close']
                ))
            
            # Three candle patterns
            if i >= 2:
                if self._is_morning_star(prev2, prev, candle):
                    self.patterns.append(Pattern(
                        type=CandlePattern.MORNING_STAR,
                        strength="strong",
                        timestamp=candle['timestamp'],
                        price=candle['close']
                    ))
                
                if self._is_evening_star(prev2, prev, candle):
                    self.patterns.append(Pattern(
                        type=CandlePattern.EVENING_STAR,
                        strength="strong",
                        timestamp=candle['timestamp'],
                        price=candle['close']
                    ))
        
        return self.patterns
    
    def _is_doji(self, candle: dict, threshold: float = 0.1) -> bool:
        """Check if candle is a doji (open ≈ close)"""
        body = abs(candle['close'] - candle['open'])
        range_size = candle['high'] - candle['low']
        if range_size == 0:
            return False
        return body / range_size < threshold
    
    def _is_hammer(self, candle: dict) -> bool:
        """Check if candle is a hammer"""
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        # Lower shadow at least 2x body, small upper shadow
        return (lower_shadow > body * 2 and 
                upper_shadow < body * 0.5 and
                candle['close'] > candle['open'])  # Bullish hammer
    
    def _is_shooting_star(self, candle: dict) -> bool:
        """Check if candle is a shooting star"""
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        # Upper shadow at least 2x body, small lower shadow
        return (upper_shadow > body * 2 and 
                lower_shadow < body * 0.5 and
                candle['close'] < candle['open'])  # Bearish shooting star
    
    def _is_engulfing_bullish(self, prev: dict, current: dict) -> bool:
        """Check for bullish engulfing pattern"""
        prev_body = abs(prev['close'] - prev['open'])
        current_body = abs(current['close'] - current['open'])
        
        return (prev['close'] < prev['open'] and  # Previous bearish
                current['close'] > current['open'] and  # Current bullish
                current['open'] < prev['close'] and  # Engulfing
                current['close'] > prev['open'])
    
    def _is_engulfing_bearish(self, prev: dict, current: dict) -> bool:
        """Check for bearish engulfing pattern"""
        return (prev['close'] > prev['open'] and  # Previous bullish
                current['close'] < current['open'] and  # Current bearish
                current['open'] > prev['close'] and  # Engulfing
                current['close'] < prev['open'])
    
    def _is_morning_star(self, first: dict, second: dict, third: dict) -> bool:
        """Check for morning star pattern"""
        return (first['close'] < first['open'] and  # First bearish
                abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.3 and  # Small second
                third['close'] > third['open'] and  # Third bullish
                third['close'] > (first['open'] + first['close']) / 2)  # Strong third
    
    def _is_evening_star(self, first: dict, second: dict, third: dict) -> bool:
        """Check for evening star pattern"""
        return (first['close'] > first['open'] and  # First bullish
                abs(second['close'] - second['open']) < abs(first['close'] - first['open']) * 0.3 and  # Small second
                third['close'] < third['open'] and  # Third bearish
                third['close'] < (first['open'] + first['close']) / 2)  # Strong third
    
    def find_support_resistance(self, lookback: int = 100, tolerance: float = 0.5) -> List[SupportResistance]:
        """Find support and resistance levels"""
        if len(self.data) < lookback:
            lookback = len(self.data)
        
        recent_data = self.data[-lookback:]
        
        # Collect swing points
        highs = []
        lows = []
        
        for i in range(2, len(recent_data) - 2):
            # Swing high
            if (recent_data[i]['high'] > recent_data[i-1]['high'] and
                recent_data[i]['high'] > recent_data[i-2]['high'] and
                recent_data[i]['high'] > recent_data[i+1]['high'] and
                recent_data[i]['high'] > recent_data[i+2]['high']):
                highs.append((recent_data[i]['high'], recent_data[i]['timestamp']))
            
            # Swing low
            if (recent_data[i]['low'] < recent_data[i-1]['low'] and
                recent_data[i]['low'] < recent_data[i-2]['low'] and
                recent_data[i]['low'] < recent_data[i+1]['low'] and
                recent_data[i]['low'] < recent_data[i+2]['low']):
                lows.append((recent_data[i]['low'], recent_data[i]['timestamp']))
        
        # Cluster levels within tolerance
        resistance_clusters = self._cluster_levels(highs, tolerance)
        support_clusters = self._cluster_levels(lows, tolerance)
        
        self.levels = []
        
        for level, touches in resistance_clusters.items():
            if len(touches) >= 2:
                self.levels.append(SupportResistance(
                    level=level,
                    type="resistance",
                    strength=len(touches),
                    last_touch=touches[-1]
                ))
        
        for level, touches in support_clusters.items():
            if len(touches) >= 2:
                self.levels.append(SupportResistance(
                    level=level,
                    type="support",
                    strength=len(touches),
                    last_touch=touches[-1]
                ))
        
        # Sort by strength
        self.levels.sort(key=lambda x: x.strength, reverse=True)
        
        return self.levels
    
    def _cluster_levels(self, levels: List[tuple], tolerance: float) -> dict:
        """Cluster price levels within tolerance"""
        clusters = {}
        
        for price, timestamp in levels:
            found = False
            for cluster_price in list(clusters.keys()):
                if abs(price - cluster_price) <= tolerance:
                    clusters[cluster_price].append(timestamp)
                    found = True
                    break
            
            if not found:
                clusters[price] = [timestamp]
        
        return clusters
    
    def analyze_trend(self) -> dict:
        """Analyze trend using moving averages"""
        if len(self.data) < 50:
            return {"direction": "neutral", "strength": 0}
        
        closes = [c['close'] for c in self.data]
        
        # Calculate EMAs
        ema_20 = self._calculate_ema(closes, 20)
        ema_50 = self._calculate_ema(closes, 50)
        
        current_price = closes[-1]
        
        # Trend direction
        if ema_20[-1] > ema_50[-1] and current_price > ema_20[-1]:
            direction = "bullish"
        elif ema_20[-1] < ema_50[-1] and current_price < ema_20[-1]:
            direction = "bearish"
        else:
            direction = "neutral"
        
        # Trend strength (ADX-like calculation)
        atr = self._calculate_atr(self.data, 14)
        price_change = abs(current_price - closes[-20]) / atr if atr > 0 else 0
        strength = min(100, price_change * 10)
        
        self.trend = {
            "direction": direction,
            "strength": round(strength, 2),
            "ema_20": round(ema_20[-1], 2),
            "ema_50": round(ema_50[-1], 2),
            "price_vs_ema20": round((current_price - ema_20[-1]) / ema_20[-1] * 100, 2)
        }
        
        return self.trend
    
    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = [sum(data[:period]) / period]
        
        for price in data[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        
        # Pad beginning
        return [ema[0]] * (period - 1) + ema
    
    def _calculate_atr(self, data: List[dict], period: int) -> float:
        """Calculate Average True Range"""
        if len(data) < period + 1:
            return 0
        
        tr_list = []
        for i in range(1, len(data)):
            high_low = data[i]['high'] - data[i]['low']
            high_close = abs(data[i]['high'] - data[i-1]['close'])
            low_close = abs(data[i]['low'] - data[i-1]['close'])
            tr_list.append(max(high_low, high_close, low_close))
        
        return np.mean(tr_list[-period:])
