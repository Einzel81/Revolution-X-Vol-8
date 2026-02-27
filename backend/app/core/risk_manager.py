# backend/app/core/risk_manager.py
"""
Risk Management System
- Kelly Criterion
- Dynamic Position Sizing
- Drawdown Protection
- Correlation Check
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import math

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskAssessment:
    can_trade: bool
    risk_level: RiskLevel
    recommended_risk_percent: float
    max_position_size: float
    reasons: List[str]

class RiskManager:
    def __init__(
        self,
        max_daily_risk: float = 0.05,        # 5% max daily risk
        max_total_risk: float = 0.10,        # 10% max total risk
        max_drawdown: float = 0.15,          # 15% max drawdown
        kelly_fraction: float = 0.25         # Quarter Kelly
    ):
        self.max_daily_risk = max_daily_risk
        self.max_total_risk = max_total_risk
        self.max_drawdown = max_drawdown
        self.kelly_fraction = kelly_fraction
        
        # State tracking
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.current_drawdown = 0.0
        self.open_positions_risk = 0.0
        
    def assess_trade(
        self,
        balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        current_positions: int,
        correlation_with_open: float = 0.0
    ) -> RiskAssessment:
        """
        Assess if we can take a new trade
        """
        reasons = []
        
        # Check drawdown
        if self.current_drawdown >= self.max_drawdown:
            return RiskAssessment(
                can_trade=False,
                risk_level=RiskLevel.CRITICAL,
                recommended_risk_percent=0,
                max_position_size=0,
                reasons=["Maximum drawdown reached"]
            )
        
        # Check daily risk limit
        daily_risk_used = abs(self.daily_pnl) / balance if balance > 0 else 0
        if daily_risk_used >= self.max_daily_risk:
            return RiskAssessment(
                can_trade=False,
                risk_level=RiskLevel.CRITICAL,
                recommended_risk_percent=0,
                max_position_size=0,
                reasons=["Daily risk limit reached"]
            )
        
        # Check correlation
        if correlation_with_open > 0.8:
            reasons.append("High correlation with open positions")
        
        # Calculate Kelly Criterion
        kelly_risk = self._calculate_kelly(win_rate, avg_win, avg_loss)
        adjusted_risk = kelly_risk * self.kelly_fraction
        
        # Adjust for number of positions
        position_factor = max(0.5, 1 - (current_positions * 0.1))
        final_risk = adjusted_risk * position_factor
        
        # Cap at max risk per trade
        final_risk = min(final_risk, 0.02)  # Max 2% per trade
        
        # Determine risk level
        if final_risk >= 0.015:
            risk_level = RiskLevel.HIGH
        elif final_risk >= 0.01:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Check if we have room for this trade
        total_risk = self.open_positions_risk + final_risk
        if total_risk > self.max_total_risk:
            final_risk = max(0, self.max_total_risk - self.open_positions_risk)
            reasons.append("Reduced size due to total risk limit")
        
        max_position_size = balance * final_risk
        
        return RiskAssessment(
            can_trade=final_risk > 0,
            risk_level=risk_level,
            recommended_risk_percent=final_risk * 100,
            max_position_size=max_position_size,
            reasons=reasons
        )
    
    def _calculate_kelly(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion: f* = (p*b - q) / b
        where:
        p = probability of win
        q = probability of loss (1-p)
        b = win/loss ratio
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.01  # Default 1%
        
        b = avg_win / avg_loss  # Win/loss ratio
        q = 1 - win_rate
        
        kelly = (win_rate * b - q) / b
        
        # Kelly can be negative, meaning don't trade
        return max(0, kelly)
    
    def update_balance(self, new_balance: float, previous_balance: float):
        """Update tracking after trade"""
        pnl = new_balance - previous_balance
        self.daily_pnl += pnl
        
        # Update peak and drawdown
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
        
        if self.peak_balance > 0:
            self.current_drawdown = (self.peak_balance - new_balance) / self.peak_balance
    
    def reset_daily(self):
        """Reset daily tracking"""
        self.daily_pnl = 0.0
    
    def get_risk_report(self) -> dict:
        """Get current risk status"""
        return {
            "daily_pnl": round(self.daily_pnl, 2),
            "current_drawdown": round(self.current_drawdown * 100, 2),
            "max_drawdown_limit": round(self.max_drawdown * 100, 2),
            "open_positions_risk": round(self.open_positions_risk * 100, 2),
            "remaining_risk_capacity": round((self.max_total_risk - self.open_positions_risk) * 100, 2)
        }
