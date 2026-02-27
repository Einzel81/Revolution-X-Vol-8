"""
Position Sizing Calculator
- Fixed Risk
- Kelly Criterion
- ATR-based sizing
- Volatility-adjusted
"""

from dataclasses import dataclass
from typing import Literal, Optional
import numpy as np

@dataclass
class PositionSize:
    lots: float
    units: int
    risk_amount: float
    risk_percent: float
    stop_loss_pips: float
    take_profit_pips: float
    risk_reward_ratio: float

class PositionSizer:
    def __init__(
        self,
        method: Literal["fixed", "kelly", "atr", "volatility"] = "kelly",
        base_risk_percent: float = 0.02,
        max_lots: float = 10.0
    ):
        self.method = method
        self.base_risk_percent = base_risk_percent
        self.max_lots = max_lots
        
        # Contract specs for XAU/USD
        self.pip_value = 1.0  # $1 per pip for 0.01 lot (1 unit)
        self.lot_size = 100   # 1 lot = 100 units
    
    def calculate(
        self,
        balance: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        atr: Optional[float] = None,
        volatility: Optional[float] = None,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> PositionSize:
        """
        Calculate position size based on method
        """
        # Calculate risk amount
        if self.method == "fixed":
            risk_amount = balance * self.base_risk_percent
            
        elif self.method == "kelly" and win_rate and avg_win and avg_loss:
            kelly = self._kelly_criterion(win_rate, avg_win, avg_loss)
            risk_amount = balance * kelly * 0.25  # Quarter Kelly
            
        elif self.method == "atr" and atr:
            # ATR-based: risk = 1.5 * ATR
            risk_pips = atr * 1.5 * 10  # Convert to pips (XAU/USD)
            risk_amount = balance * self.base_risk_percent
            
        elif self.method == "volatility" and volatility:
            # Reduce size in high volatility
            vol_factor = max(0.5, 1 - (volatility / 100))
            risk_amount = balance * self.base_risk_percent * vol_factor
            
        else:
            risk_amount = balance * self.base_risk_percent
        
        # Calculate distance to stop loss in pips
        # XAU/USD: 1 pip = 0.1
        sl_distance = abs(entry_price - stop_loss)
        sl_pips = sl_distance * 10  # Convert to pips
        
        if sl_pips == 0:
            raise ValueError("Stop loss cannot be at entry price")
        
        # Calculate lots
        # risk = lots * pip_value * sl_pips
        # lots = risk / (pip_value * sl_pips)
        lots = risk_amount / (self.pip_value * sl_pips)
        
        # Apply limits
        lots = min(lots, self.max_lots)
        lots = max(0.01, lots)  # Minimum 0.01 lot
        
        # Round to 2 decimal places
        lots = round(lots, 2)
        
        # Calculate units
        units = int(lots * self.lot_size)
        
        # Recalculate actual risk
        actual_risk = lots * self.pip_value * sl_pips
        risk_percent = (actual_risk / balance) * 100 if balance > 0 else 0
        
        # Calculate TP distance
        tp_distance = abs(take_profit - entry_price)
        tp_pips = tp_distance * 10
        
        # R:R ratio
        rr_ratio = tp_pips / sl_pips if sl_pips > 0 else 0
        
        return PositionSize(
            lots=lots,
            units=units,
            risk_amount=round(actual_risk, 2),
            risk_percent=round(risk_percent, 2),
            stop_loss_pips=round(sl_pips, 1),
            take_profit_pips=round(tp_pips, 1),
            risk_reward_ratio=round(rr_ratio, 2)
        )
    
    def _kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly fraction"""
        if avg_loss == 0:
            return 0.01
        
        b = avg_win / avg_loss
        q = 1 - win_rate
        
        kelly = (win_rate * b - q) / b
        return max(0.01, kelly)  # Minimum 1%
    
    def adjust_for_correlation(
        self,
        base_size: PositionSize,
        correlation: float,
        num_similar_positions: int
    ) -> PositionSize:
        """
        Reduce size if highly correlated with existing positions
        """
        # Reduce by 20% for each similar correlated position
        reduction = min(0.8, correlation * num_similar_positions * 0.2)
        factor = 1 - reduction
        
        adjusted_lots = round(base_size.lots * factor, 2)
        
        return PositionSize(
            lots=adjusted_lots,
            units=int(adjusted_lots * self.lot_size),
            risk_amount=round(base_size.risk_amount * factor, 2),
            risk_percent=round(base_size.risk_percent * factor, 2),
            stop_loss_pips=base_size.stop_loss_pips,
            take_profit_pips=base_size.take_profit_pips,
            risk_reward_ratio=base_size.risk_reward_ratio
        )
