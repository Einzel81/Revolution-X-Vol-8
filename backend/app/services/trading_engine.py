# backend/app/core/trading_engine.py
"""
Trading Engine - Main execution logic
Combines all strategies and risk management
"""

from typing import Optional, List, Dict
from datetime import datetime
import asyncio

from app.strategies.smc import SMCAnalyzer
from app.strategies.volume_profile import VolumeProfileAnalyzer
from app.strategies.price_action import PriceActionAnalyzer
from app.strategies.kill_zones import KillZoneAnalyzer
from app.core.risk_manager import RiskManager
from app.core.position_sizer import PositionSizer
from app.mt5.connector import mt5_connector

class TradingEngine:
    def __init__(self):
        self.smc = None
        self.volume_profile = None
        self.price_action = None
        self.kill_zones = KillZoneAnalyzer()
        self.risk_manager = RiskManager()
        self.position_sizer = PositionSizer(method="kelly")
        
        self.is_running = False
        self.current_signal = None
        
    async def analyze_market(self, data: List[dict], symbol: str = "XAUUSD") -> Dict:
        """
        Run full market analysis
        """
        # Initialize analyzers
        self.smc = SMCAnalyzer(data)
        self.volume_profile = VolumeProfileAnalyzer(data)
        self.price_action = PriceActionAnalyzer(data)
        
        # Run all analyses
        smc_result = self.smc.analyze()
        vp_result = self.volume_profile.calculate()
        pa_result = self.price_action.analyze()
        kz_result = self.kill_zones.should_trade()
        
        # Combine signals
        signal = self._generate_signal(
            smc_result, vp_result, pa_result, kz_result, symbol
        )
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "signal": signal,
            "smc": smc_result,
            "volume_profile": vp_result,
            "price_action": pa_result,
            "kill_zone": kz_result
        }
    
    def _generate_signal(
        self,
        smc: Dict,
        vp: Optional[object],
        pa: Dict,
        kz: Dict,
        symbol: str
    ) -> Dict:
        """
        Generate trading signal from all analyses
        """
        if not kz.get("can_trade", False):
            return {
                "action": "WAIT",
                "confidence": 0,
                "reason": "Outside optimal trading hours",
                "details": kz.get("reasons", [])
            }
        
        # Score components
        score = 0
        reasons = []
        
        # SMC Score
        bullish_obs = [ob for ob in smc.get("order_blocks", []) 
                      if ob.type.value == "bullish" and ob.strength in ["strong", "very_strong"]]
        bearish_obs = [ob for ob in smc.get("order_blocks", []) 
                      if ob.type.value == "bearish" and ob.strength in ["strong", "very_strong"]]
        
        if bullish_obs:
            score += 30
            reasons.append(f"Strong bullish OB at {bullish_obs[0].low:.2f}")
        if bearish_obs:
            score -= 30
            reasons.append(f"Strong bearish OB at {bearish_obs[0].high:.2f}")
        
        # Volume Profile Score
        if vp:
            price_position = self.volume_profile.get_price_position(
                self.smc.data[-1]['close'] if self.smc.data else 0
            )
            if price_position == "below_value_area":
                score += 20
                reasons.append("Price below value area (potential long)")
            elif price_position == "above_value_area":
                score -= 20
                reasons.append("Price above value area (potential short)")
        
        # Price Action Score
        trend = pa.get("trend", {})
        if trend.get("direction") == "bullish":
            score += 20
            reasons.append("Bullish trend")
        elif trend.get("direction") == "bearish":
            score -= 20
            reasons.append("Bearish trend")
        
        # Patterns
        patterns = pa.get("patterns", [])
        recent_patterns = patterns[-3:] if len(patterns) > 3 else patterns
        
        for pattern in recent_patterns:
            if pattern.type.value in ["engulfing_bullish", "morning_star", "hammer"]:
                score += 15
                reasons.append(f"Bullish pattern: {pattern.type.value}")
            elif pattern.type.value in ["engulfing_bearish", "evening_star", "shooting_star"]:
                score -= 15
                reasons.append(f"Bearish pattern: {pattern.type.value}")
        
        # Determine action
        if score >= 60:
            action = "STRONG_BUY"
        elif score >= 40:
            action = "BUY"
        elif score <= -60:
            action = "STRONG_SELL"
        elif score <= -40:
            action = "SELL"
        else:
            action = "NEUTRAL"
        
        confidence = min(100, abs(score))
        
        return {
            "action": action,
            "confidence": confidence,
            "score": score,
            "reasons": reasons,
            "entry_price": self.smc.data[-1]['close'] if self.smc.data else None,
            "suggested_sl": self._calculate_sl(action, smc),
            "suggested_tp": self._calculate_tp(action, smc),
            "kill_zone": kz
        }
    
    def _calculate_sl(self, action: str, smc: Dict) -> Optional[float]:
        """Calculate suggested stop loss"""
        if not self.smc or not self.smc.data:
            return None
        
        current_price = self.smc.data[-1]['close']
        
        if "BUY" in action:
            # Find nearest bullish OB or use ATR
            bullish_obs = [ob for ob in smc.get("order_blocks", []) 
                          if ob.type.value == "bullish"]
            if bullish_obs:
                return min(ob.low for ob in bullish_obs) - 5  # 5 pips buffer
            else:
                return current_price * 0.995  # 0.5% stop
        else:
            bearish_obs = [ob for ob in smc.get("order_blocks", []) 
                          if ob.type.value == "bearish"]
            if bearish_obs:
                return max(ob.high for ob in bearish_obs) + 5
            else:
                return current_price * 1.005
        
        return None
    
    def _calculate_tp(self, action: str, smc: Dict) -> Optional[float]:
        """Calculate suggested take profit"""
        if not self.smc or not self.smc.data:
            return None
        
        current_price = self.smc.data[-1]['close']
        sl = self._calculate_sl(action, smc)
        
        if sl is None:
            return None
        
        # R:R = 1:2
        risk = abs(current_price - sl)
        
        if "BUY" in action:
            return current_price + (risk * 2)
        else:
            return current_price - (risk * 2)
    
    async def execute_trade(
        self,
        signal: Dict,
        balance: float,
        win_rate: float = 0.55,
        avg_win: float = 100,
        avg_loss: float = 50
    ) -> Dict:
        """
        Execute trade based on signal
        """
        action = signal.get("action", "NEUTRAL")
        
        if "NEUTRAL" in action:
            return {"status": "skipped", "reason": "Neutral signal"}
        
        # Risk assessment
        risk_assessment = self.risk_manager.assess_trade(
            balance=balance,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            current_positions=0  # TODO: Get actual count
        )
        
        if not risk_assessment.can_trade:
            return {
                "status": "rejected",
                "reason": "Risk management",
                "details": risk_assessment.reasons
            }
        
        # Calculate position size
        entry = signal.get("entry_price")
        sl = signal.get("suggested_sl")
        tp = signal.get("suggested_tp")
        
        if not all([entry, sl, tp]):
            return {"status": "error", "reason": "Missing price levels"}
        
        try:
            position = self.position_sizer.calculate(
                balance=balance,
                entry_price=entry,
                stop_loss=sl,
                take_profit=tp,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss
            )
        except ValueError as e:
            return {"status": "error", "reason": str(e)}
        
        # Determine direction
        direction = "BUY" if "BUY" in action else "SELL"
        
        # Execute via MT5
        # TODO: Implement actual execution
        # result = await mt5_connector.send_order(
        #     symbol="XAUUSD",
        #     action=direction,
        #     volume=position.lots,
        #     sl=sl,
        #     tp=tp
        # )
        
        return {
            "status": "simulated",
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "position_size": {
                "lots": position.lots,
                "risk_amount": position.risk_amount,
                "risk_percent": position.risk_percent,
                "r_r": position.risk_reward_ratio
            },
            "confidence": signal.get("confidence"),
            "risk_assessment": {
                "level": risk_assessment.risk_level.value,
                "reasons": risk_assessment.reasons
            }
        }
    
    async def start(self):
        """Start trading engine"""
        self.is_running = True
        while self.is_running:
            # Main trading loop
            await asyncio.sleep(1)
    
    def stop(self):
        """Stop trading engine"""
        self.is_running = False
