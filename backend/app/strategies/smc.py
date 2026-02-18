# backend/app/strategies/smc.py
"""
Smart Money Concepts (SMC) Strategy
- Order Blocks
- Fair Value Gaps (FVG)
- Liquidity Sweeps
- Market Structure
"""

from dataclasses import dataclass
from typing import List, Optional, Literal
from enum import Enum
import numpy as np

class OrderBlockType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"

class FVGType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"

@dataclass
class OrderBlock:
    type: OrderBlockType
    high: float
    low: float
    open: float
    close: float
    volume: float
    timestamp: str
    strength: str  # weak, moderate, strong, very_strong
    is_active: bool = True
    
    def __repr__(self):
        return f"OB({self.type.value}, {self.low:.2f}-{self.high:.2f}, {self.strength})"

@dataclass
class FairValueGap:
    type: FVGType
    top: float
    bottom: float
    timestamp: str
    is_filled: bool = False
    
    @property
    def height(self) -> float:
        return self.top - self.bottom

@dataclass
class LiquiditySweep:
    type: Literal["high", "low"]
    level: float
    timestamp: str
    volume: float
    confirmed: bool = False

class SMCAnalyzer:
    def __init__(self, data: List[dict]):
        """
        data: List of OHLCV candles
        [
            {
                'timestamp': '2026-02-18T14:30:00',
                'open': 2945.50,
                'high': 2950.00,
                'low': 2942.00,
                'close': 2948.50,
                'volume': 1500
            },
            ...
        ]
        """
        self.data = data
        self.order_blocks: List[OrderBlock] = []
        self.fvgs: List[FairValueGap] = []
        self.liquidity_sweeps: List[LiquiditySweep] = []
        
    def analyze(self) -> dict:
        """Run full SMC analysis"""
        self.detect_order_blocks()
        self.detect_fvg()
        self.detect_liquidity_sweeps()
        self.analyze_market_structure()
        
        return {
            "order_blocks": self.order_blocks,
            "fvgs": self.fvgs,
            "liquidity_sweeps": self.liquidity_sweeps,
            "market_structure": self.market_structure
        }
    
    def detect_order_blocks(self, lookback: int = 50) -> List[OrderBlock]:
        """
        Detect Order Blocks based on the last candle before a strong move
        """
        if len(self.data) < lookback:
            lookback = len(self.data)
        
        recent_data = self.data[-lookback:]
        self.order_blocks = []
        
        for i in range(1, len(recent_data) - 1):
            prev = recent_data[i - 1]
            current = recent_data[i]
            next_candle = recent_data[i + 1]
            
            # Bullish Order Block: last bearish candle before strong bullish move
            if (current['close'] < current['open'] and  # Bearish candle
                next_candle['close'] > next_candle['open'] and  # Next is bullish
                next_candle['close'] > current['high']):  # Strong move up
                
                strength = self._calculate_ob_strength(current, next_candle, 'bullish')
                
                ob = OrderBlock(
                    type=OrderBlockType.BULLISH,
                    high=current['high'],
                    low=current['low'],
                    open=current['open'],
                    close=current['close'],
                    volume=current['volume'],
                    timestamp=current['timestamp'],
                    strength=strength
                )
                self.order_blocks.append(ob)
            
            # Bearish Order Block: last bullish candle before strong bearish move
            elif (current['close'] > current['open'] and  # Bullish candle
                  next_candle['close'] < next_candle['open'] and  # Next is bearish
                  next_candle['close'] < current['low']):  # Strong move down
                
                strength = self._calculate_ob_strength(current, next_candle, 'bearish')
                
                ob = OrderBlock(
                    type=OrderBlockType.BEARISH,
                    high=current['high'],
                    low=current['low'],
                    open=current['open'],
                    close=current['close'],
                    volume=current['volume'],
                    timestamp=current['timestamp'],
                    strength=strength
                )
                self.order_blocks.append(ob)
        
        # Sort by strength and recency
        strength_order = {'very_strong': 4, 'strong': 3, 'moderate': 2, 'weak': 1}
        self.order_blocks.sort(
            key=lambda x: (strength_order.get(x.strength, 0), x.timestamp),
            reverse=True
        )
        
        return self.order_blocks
    
    def _calculate_ob_strength(self, ob_candle: dict, move_candle: dict, ob_type: str) -> str:
        """Calculate Order Block strength"""
        # Volume analysis
        avg_volume = np.mean([d['volume'] for d in self.data[-20:]])
        volume_ratio = ob_candle['volume'] / avg_volume if avg_volume > 0 else 1
        
        # Move strength
        if ob_type == 'bullish':
            move_size = (move_candle['close'] - ob_candle['high']) / ob_candle['high'] * 100
        else:
            move_size = (ob_candle['low'] - move_candle['close']) / ob_candle['low'] * 100
        
        # Score
        score = 0
        if volume_ratio > 2.0:
            score += 2
        elif volume_ratio > 1.5:
            score += 1
        
        if move_size > 1.0:
            score += 2
        elif move_size > 0.5:
            score += 1
        
        if score >= 4:
            return "very_strong"
        elif score >= 3:
            return "strong"
        elif score >= 2:
            return "moderate"
        else:
            return "weak"
    
    def detect_fvg(self, min_gap_size: float = 0.1) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (imbalances)
        """
        self.fvgs = []
        
        for i in range(len(self.data) - 2):
            candle_1 = self.data[i]
            candle_2 = self.data[i + 1]
            candle_3 = self.data[i + 2]
            
            # Bullish FVG: candle 2 low > candle 1 high
            if candle_2['low'] > candle_1['high']:
                gap_size = candle_2['low'] - candle_1['high']
                if gap_size >= min_gap_size:
                    fvg = FairValueGap(
                        type=FVGType.BULLISH,
                        top=candle_2['low'],
                        bottom=candle_1['high'],
                        timestamp=candle_2['timestamp']
                    )
                    self.fvgs.append(fvg)
            
            # Bearish FVG: candle 2 high < candle 1 low
            elif candle_2['high'] < candle_1['low']:
                gap_size = candle_1['low'] - candle_2['high']
                if gap_size >= min_gap_size:
                    fvg = FairValueGap(
                        type=FVGType.BEARISH,
                        top=candle_1['low'],
                        bottom=candle_2['high'],
                        timestamp=candle_2['timestamp']
                    )
                    self.fvgs.append(fvg)
        
        # Check if FVGs are filled
        current_price = self.data[-1]['close']
        for fvg in self.fvgs:
            if fvg.type == FVGType.BULLISH:
                fvg.is_filled = current_price <= fvg.bottom
            else:
                fvg.is_filled = current_price >= fvg.top
        
        return self.fvgs
    
    def detect_liquidity_sweeps(self, swing_lookback: int = 20) -> List[LiquiditySweep]:
        """
        Detect liquidity sweeps (stop hunts)
        """
        self.liquidity_sweeps = []
        
        if len(self.data) < swing_lookback + 5:
            return self.liquidity_sweeps
        
        # Find swing highs and lows
        recent_data = self.data[-swing_lookback-5:-5]
        
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(recent_data) - 2):
            # Swing high
            if (recent_data[i]['high'] > recent_data[i-1]['high'] and
                recent_data[i]['high'] > recent_data[i-2]['high'] and
                recent_data[i]['high'] > recent_data[i+1]['high'] and
                recent_data[i]['high'] > recent_data[i+2]['high']):
                swing_highs.append((i, recent_data[i]['high']))
            
            # Swing low
            if (recent_data[i]['low'] < recent_data[i-1]['low'] and
                recent_data[i]['low'] < recent_data[i-2]['low'] and
                recent_data[i]['low'] < recent_data[i+1]['low'] and
                recent_data[i]['low'] < recent_data[i+2]['low']):
                swing_lows.append((i, recent_data[i]['low']))
        
        # Check for sweeps in last 5 candles
        last_candles = self.data[-5:]
        
        # High sweep
        for idx, level in swing_highs[-3:]:  # Last 3 swing highs
            for candle in last_candles:
                if candle['high'] > level * 1.001:  # Slight break above
                    # Check if closed back below
                    if candle['close'] < level:
                        sweep = LiquiditySweep(
                            type="high",
                            level=level,
                            timestamp=candle['timestamp'],
                            volume=candle['volume'],
                            confirmed=True
                        )
                        self.liquidity_sweeps.append(sweep)
                        break
        
        # Low sweep
        for idx, level in swing_lows[-3:]:  # Last 3 swing lows
            for candle in last_candles:
                if candle['low'] < level * 0.999:  # Slight break below
                    # Check if closed back above
                    if candle['close'] > level:
                        sweep = LiquiditySweep(
                            type="low",
                            level=level,
                            timestamp=candle['timestamp'],
                            volume=candle['volume'],
                            confirmed=True
                        )
                        self.liquidity_sweeps.append(sweep)
                        break
        
        return self.liquidity_sweeps
    
    def analyze_market_structure(self) -> dict:
        """
        Analyze market structure (BOS/CHoCH)
        """
        if len(self.data) < 20:
            self.market_structure = {"trend": "neutral", "structure": []}
            return self.market_structure
        
        recent = self.data[-20:]
        
        # Find higher highs and higher lows (uptrend)
        # or lower highs and lower lows (downtrend)
        
        highs = [c['high'] for c in recent]
        lows = [c['low'] for c in recent]
        
        hh = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
        hl = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
        lh = sum(1 for i in range(1, len(highs)) if highs[i] < highs[i-1])
        ll = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
        
        if hh > lh and hl > ll:
            trend = "bullish"
        elif lh > hh and ll > hl:
            trend = "bearish"
        else:
            trend = "neutral"
        
        # Detect structure breaks
        structure_points = []
        
        # Break of Structure (BOS)
        last_major_high = max(highs[:-5]) if len(highs) > 5 else highs[0]
        last_major_low = min(lows[:-5]) if len(lows) > 5 else lows[0]
        
        if recent[-1]['close'] > last_major_high:
            structure_points.append({
                "type": "BOS",
                "direction": "bullish",
                "price": recent[-1]['close'],
                "timestamp": recent[-1]['timestamp']
            })
        elif recent[-1]['close'] < last_major_low:
            structure_points.append({
                "type": "BOS",
                "direction": "bearish",
                "price": recent[-1]['close'],
                "timestamp": recent[-1]['timestamp']
            })
        
        self.market_structure = {
            "trend": trend,
            "structure": structure_points,
            "hh_count": hh,
            "hl_count": hl,
            "lh_count": lh,
            "ll_count": ll
        }
        
        return self.market_structure
    
    def get_nearest_ob(self, price: float, ob_type: Optional[OrderBlockType] = None) -> Optional[OrderBlock]:
        """Get nearest Order Block to current price"""
        active_obs = [ob for ob in self.order_blocks if ob.is_active]
        
        if ob_type:
            active_obs = [ob for ob in active_obs if ob.type == ob_type]
        
        if not active_obs:
            return None
        
        # Find nearest
        nearest = min(active_obs, key=lambda ob: abs(
            (ob.high + ob.low) / 2 - price
        ))
        
        return nearest
    
    def get_unfilled_fvgs(self) -> List[FairValueGap]:
        """Get all unfilled Fair Value Gaps"""
        return [fvg for fvg in self.fvgs if not fvg.is_filled]
