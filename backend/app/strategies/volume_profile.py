# backend/app/strategies/volume_profile.py
"""
Volume Profile Analysis
- Point of Control (POC)
- Value Area High (VAH)
- Value Area Low (VAL)
- Volume Nodes (HVN/LVN)
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
import numpy as np
from collections import defaultdict

@dataclass
class VolumeNode:
    price_level: float
    volume: float
    type: str  # HVN (High Volume Node) or LVN (Low Volume Node)

@dataclass
class VolumeProfile:
    poc: float  # Point of Control (highest volume level)
    vah: float  # Value Area High (70th percentile)
    val: float  # Value Area Low (30th percentile)
    value_area_volume: float
    total_volume: float
    nodes: List[VolumeNode]
    
    @property
    def value_area_width(self) -> float:
        return self.vah - self.val

class VolumeProfileAnalyzer:
    def __init__(self, data: List[dict], row_size: float = 1.0):
        """
        data: OHLCV candles
        row_size: Price range for each volume row (e.g., $1 for gold)
        """
        self.data = data
        self.row_size = row_size
        self.profile: VolumeProfile = None
        
    def calculate(self) -> VolumeProfile:
        """Calculate full Volume Profile"""
        if not self.data:
            return None
        
        # Build volume histogram
        price_volume = defaultdict(float)
        
        for candle in self.data:
            # Distribute volume across the candle's range
            low = candle['low']
            high = candle['high']
            volume = candle['volume']
            
            # Number of rows this candle spans
            num_rows = max(1, int((high - low) / self.row_size))
            volume_per_row = volume / num_rows
            
            # Add volume to each price level
            for i in range(num_rows):
                price_level = low + (i * self.row_size)
                price_volume[price_level] += volume_per_row
        
        # Sort by price
        sorted_levels = sorted(price_volume.items())
        prices = [p for p, v in sorted_levels]
        volumes = [v for p, v in sorted_levels]
        
        if not prices:
            return None
        
        total_volume = sum(volumes)
        
        # Find POC (highest volume level)
        max_volume_idx = np.argmax(volumes)
        poc = prices[max_volume_idx]
        
        # Calculate Value Area (70% of volume)
        poc_volume = volumes[max_volume_idx]
        value_area_volume = total_volume * 0.70
        
        # Expand from POC until we reach 70% of volume
        current_volume = poc_volume
        vah_idx = max_volume_idx
        val_idx = max_volume_idx
        
        while current_volume < value_area_volume:
            expanded = False
            
            # Try to expand up
            if vah_idx < len(volumes) - 1:
                vah_idx += 1
                current_volume += volumes[vah_idx]
                expanded = True
            
            # Try to expand down
            if val_idx > 0:
                val_idx -= 1
                current_volume += volumes[val_idx]
                expanded = True
            
            if not expanded:
                break
        
        vah = prices[vah_idx]
        val = prices[val_idx]
        
        # Identify High and Low Volume Nodes
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        nodes = []
        for price, volume in sorted_levels:
            if volume > avg_volume + std_volume:
                nodes.append(VolumeNode(price, volume, "HVN"))
            elif volume < avg_volume - std_volume:
                nodes.append(VolumeNode(price, volume, "LVN"))
        
        self.profile = VolumeProfile(
            poc=poc,
            vah=vah,
            val=val,
            value_area_volume=current_volume,
            total_volume=total_volume,
            nodes=nodes
        )
        
        return self.profile
    
    def get_price_position(self, current_price: float) -> str:
        """Get position of current price relative to Value Area"""
        if not self.profile:
            return "unknown"
        
        if current_price > self.profile.vah:
            return "above_value_area"
        elif current_price < self.profile.val:
            return "below_value_area"
        else:
            return "inside_value_area"
    
    def get_nearest_hvn(self, price: float) -> float:
        """Get nearest High Volume Node"""
        if not self.profile or not self.profile.nodes:
            return price
        
        hvns = [n for n in self.profile.nodes if n.type == "HVN"]
        if not hvns:
            return price
        
        nearest = min(hvns, key=lambda n: abs(n.price_level - price))
        return nearest.price_level
    
    def get_volume_delta(self) -> Dict:
        """Calculate volume delta (buying vs selling pressure)"""
        if len(self.data) < 2:
            return {"bias": "neutral", "delta_percent": 0}
        
        buy_volume = 0
        sell_volume = 0
        
        for candle in self.data:
            if candle['close'] > candle['open']:
                buy_volume += candle['volume']
            elif candle['close'] < candle['open']:
                sell_volume += candle['volume']
            else:
                # Neutral candle - split volume
                buy_volume += candle['volume'] / 2
                sell_volume += candle['volume'] / 2
        
        total = buy_volume + sell_volume
        if total == 0:
            return {"bias": "neutral", "delta_percent": 0}
        
        delta = buy_volume - sell_volume
        delta_percent = (abs(delta) / total) * 100
        
        if delta > 0:
            bias = "bullish"
        elif delta < 0:
            bias = "bearish"
        else:
            bias = "neutral"
        
        return {
            "bias": bias,
            "delta_percent": round(delta_percent, 2),
            "buy_volume": round(buy_volume, 2),
            "sell_volume": round(sell_volume, 2)
        }
