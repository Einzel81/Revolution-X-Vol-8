"""
DXY Index Tracker
Real-time monitoring of US Dollar Index
Revolution X - DXY Guardian
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class DXYLevel:
    price: float
    type: str  # 'support', 'resistance', 'pivot'
    strength: float  # 0-1
    touches: int

@dataclass
class DXYAlert:
    level_type: str
    price: float
    message: str
    timestamp: datetime
    severity: str  # 'info', 'warning', 'critical'

class DXYTracker:
    """
    Tracks DXY index with key levels and alerts
    """
    
    KEY_LEVELS = {
        'major_resistance': [110.0, 109.0, 108.0],
        'minor_resistance': [107.5, 107.0, 106.5],
        'pivot': 105.0,
        'minor_support': [104.5, 104.0, 103.5],
        'major_support': [103.0, 102.0, 100.0]
    }
    
    def __init__(self, 
                 alert_callback: Optional[Callable] = None,
                 check_interval_seconds: int = 60):
        self.alert_callback = alert_callback
        self.check_interval = check_interval_seconds
        self.current_price: Optional[float] = None
        self.price_history: List[Dict] = []
        self.active_levels: List[DXYLevel] = []
        self.alerts: List[DXYAlert] = []
        self.trend: str = 'neutral'
        self.momentum: float = 0
        
        self._init_levels()
    
    def _init_levels(self):
        """Initialize key levels"""
        for price in self.KEY_LEVELS['major_resistance']:
            self.active_levels.append(DXYLevel(
                price=price, type='resistance', strength=1.0, touches=0
            ))
        
        for price in self.KEY_LEVELS['minor_resistance']:
            self.active_levels.append(DXYLevel(
                price=price, type='resistance', strength=0.7, touches=0
            ))
        
        self.active_levels.append(DXYLevel(
            price=self.KEY_LEVELS['pivot'], type='pivot', strength=1.0, touches=0
        ))
        
        for price in self.KEY_LEVELS['minor_support']:
            self.active_levels.append(DXYLevel(
                price=price, type='support', strength=0.7, touches=0
            ))
        
        for price in self.KEY_LEVELS['major_support']:
            self.active_levels.append(DXYLevel(
                price=price, type='support', strength=1.0, touches=0
            ))
    
    async def start_monitoring(self, data_fetcher):
        """Start continuous monitoring"""
        while True:
            try:
                await self._check_price(data_fetcher)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"DXY monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _check_price(self, data_fetcher):
        """Check current price and generate alerts"""
        # Fetch DXY data
        df = await data_fetcher('DXY', timeframe='1m', limit=100)
        
        if df is None or len(df) == 0:
            return
        
        current = df['close'].iloc[-1]
        self.current_price = current
        
        # Update history
        self.price_history.append({
            'timestamp': datetime.now(),
            'price': current,
            'open': df['open'].iloc[-1],
            'high': df['high'].iloc[-1],
            'low': df['low'].iloc[-1]
        })
        
        # Keep last 1000 points
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
        
        # Update trend
        self._update_trend(df)
        
        # Check level proximity
        self._check_level_proximity(current)
        
        # Check breakouts
        self._check_breakouts(current, df)
    
    def _update_trend(self, df: pd.DataFrame):
        """Update trend analysis"""
        # EMA trend
        ema_20 = df['close'].ewm(span=20).mean().iloc[-1]
        ema_50 = df['close'].ewm(span=50).mean().iloc[-1]
        
        if self.current_price > ema_20 > ema_50:
            self.trend = 'bullish'
        elif self.current_price < ema_20 < ema_50:
            self.trend = 'bearish'
        else:
            self.trend = 'neutral'
        
        # Momentum
        returns = df['close'].pct_change().dropna()
        self.momentum = returns.iloc[-10:].mean() * 100
    
    def _check_level_proximity(self, current: float):
        """Check if price is near key levels"""
        for level in self.active_levels:
            distance = abs(current - level.price) / current * 100
            
            if distance < 0.1:  # Within 0.1%
                alert = DXYAlert(
                    level_type=level.type,
                    price=level.price,
                    message=f"DXY at {level.type} level {level.price}",
                    timestamp=datetime.now(),
                    severity='warning' if level.strength == 1.0 else 'info'
                )
                self._trigger_alert(alert)
                level.touches += 1
    
    def _check_breakouts(self, current: float, df: pd.DataFrame):
        """Check for level breakouts"""
        if len(self.price_history) < 2:
            return
        
        prev_price = self.price_history[-2]['price']
        
        for level in self.active_levels:
            # Break above resistance
            if level.type == 'resistance':
                if prev_price < level.price <= current:
                    alert = DXYAlert(
                        level_type='breakout',
                        price=level.price,
                        message=f"🚨 DXY broke above resistance at {level.price}! Bearish for Gold",
                        timestamp=datetime.now(),
                        severity='critical'
                    )
                    self._trigger_alert(alert)
            
            # Break below support
            elif level.type == 'support':
                if prev_price > level.price >= current:
                    alert = DXYAlert(
                        level_type='breakdown',
                        price=level.price,
                        message=f"🚨 DXY broke below support at {level.price}! Bullish for Gold",
                        timestamp=datetime.now(),
                        severity='critical'
                    )
                    self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: DXYAlert):
        """Trigger alert callback"""
        self.alerts.append(alert)
        
        # Keep last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        if self.alert_callback:
            asyncio.create_task(self.alert_callback(alert))
    
    def get_status(self) -> Dict:
        """Get current DXY status"""
        return {
            'current_price': self.current_price,
            'trend': self.trend,
            'momentum': round(self.momentum, 4),
            'nearest_levels': self._get_nearest_levels(),
            'recent_alerts': [
                {
                    'type': a.level_type,
                    'price': a.price,
                    'message': a.message,
                    'time': a.timestamp.isoformat(),
                    'severity': a.severity
                }
                for a in self.alerts[-5:]
            ]
        }
    
    def _get_nearest_levels(self) -> List[Dict]:
        """Get nearest support/resistance levels"""
        if self.current_price is None:
            return []
        
        levels = []
        for level in self.active_levels:
            distance = abs(self.current_price - level.price)
            levels.append({
                'price': level.price,
                'type': level.type,
                'distance': round(distance, 2),
                'strength': level.strength
            })
        
        # Sort by distance
        levels.sort(key=lambda x: x['distance'])
        return levels[:5]
    
    def get_impact_on_gold(self) -> Dict:
        """Analyze impact on Gold"""
        if self.current_price is None:
            return {'impact': 'unknown', 'correlation': 0}
        
        impact = 'neutral'
        strength = 'low'
        
        # Strong dollar is bearish for gold
        if self.trend == 'bullish' and self.momentum > 0.05:
            impact = 'bearish'
            strength = 'strong' if self.current_price > 107 else 'moderate'
        elif self.trend == 'bearish' and self.momentum < -0.05:
            impact = 'bullish'
            strength = 'strong' if self.current_price < 103 else 'moderate'
        
        return {
            'impact': impact,
            'strength': strength,
            'current_dxy': self.current_price,
            'recommendation': self._get_gold_recommendation(impact, strength)
        }
    
    def _get_gold_recommendation(self, impact: str, strength: str) -> str:
        """Get trading recommendation for Gold"""
        if impact == 'bearish' and strength == 'strong':
            return "Consider reducing Gold longs or hedging"
        elif impact == 'bearish':
            return "Caution on new Gold longs"
        elif impact == 'bullish' and strength == 'strong':
            return "Favorable conditions for Gold longs"
        elif impact == 'bullish':
            return "Moderate support for Gold longs"
        else:
            return "No clear directional bias from DXY"
