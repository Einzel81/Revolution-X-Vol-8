# backend/app/core/trading_engine.py
"""
Trading Engine - Main execution logic
Combines all strategies and risk management
(Updated: timeframe + db plumbing for AI registry inference)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.strategies.smc import SMCAnalyzer
from app.strategies.volume_profile import VolumeProfileAnalyzer
from app.strategies.price_action import PriceActionAnalyzer
from app.strategies.kill_zones import KillZoneAnalyzer
from app.core.risk_manager import RiskManager
from app.core.position_sizer import PositionSizer
from app.mt5.connector import mt5_connector

from app.adaptive.router import AdaptiveStrategyRouter


def _ema(values: List[float], span: int) -> Optional[float]:
    if not values or span <= 1:
        return None
    alpha = 2.0 / (span + 1.0)
    ema = float(values[0])
    for v in values[1:]:
        ema = alpha * float(v) + (1 - alpha) * ema
    return ema


def _atr_pct(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
    n = min(len(highs), len(lows), len(closes))
    if n < period + 1:
        return None
    trs = []
    for i in range(1, n):
        h = float(highs[i])
        l = float(lows[i])
        pc = float(closes[i - 1])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    if len(trs) < period:
        return None
    atr = sum(trs[-period:]) / float(period)
    last_close = float(closes[-1])
    if last_close == 0:
        return None
    return atr / last_close


def _bb_width(closes: List[float], period: int = 20, k: float = 2.0) -> Optional[float]:
    if len(closes) < period:
        return None
    window = [float(x) for x in closes[-period:]]
    m = sum(window) / float(period)
    var = sum((x - m) ** 2 for x in window) / float(period)
    sd = math.sqrt(var)
    if m == 0:
        return None
    upper = m + k * sd
    lower = m - k * sd
    return (upper - lower) / m


class FeatureVector(dict):
    """
    Minimal feature container to feed AI registry inference safely.
    Also compatible with dict access in runtime mapping.
    """
    pass


class TradingEngine:
    def __init__(self):
        self.smc = None
        self.volume_profile = None
        self.price_action = None
        self.kill_zones = KillZoneAnalyzer()
        self.risk_manager = RiskManager()
        self.position_sizer = PositionSizer(method="kelly")

        self.router = AdaptiveStrategyRouter()

        self.is_running = False
        self.current_signal = None

    async def analyze_market(
        self,
        data: List[dict],
        symbol: str = "XAUUSD",
        timeframe: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Run full market analysis.
        Updated:
          - Accept timeframe/db for AI registry inference
          - Pass context into AdaptiveStrategyRouter (AI-aware scoring)
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

        # Base signal (SMC/VP/PA/KZ)
        base_signal = self._generate_signal(
            smc_result, vp_result, pa_result, kz_result, symbol
        )

        # Build minimal features from candles for AI inference
        closes = [float(c.get("close", 0.0)) for c in data if c.get("close") is not None]
        highs = [float(c.get("high", 0.0)) for c in data if c.get("high") is not None]
        lows = [float(c.get("low", 0.0)) for c in data if c.get("low") is not None]

        last_close = closes[-1] if closes else None
        ema20 = _ema(closes[-200:] if len(closes) > 50 else closes, 20) if closes else None
        ema50 = _ema(closes[-300:] if len(closes) > 100 else closes, 50) if closes else None

        ema_spread = None
        if ema20 is not None and ema50 is not None and last_close:
            # normalized spread
            ema_spread = (ema20 - ema50) / float(last_close)

        feats = FeatureVector({
            "last_close": last_close,
            "ema20": ema20,
            "ema50": ema50,
            "ema_spread": ema_spread,
            "atr_pct": _atr_pct(highs, lows, closes, period=14),
            "bb_width": _bb_width(closes, period=20, k=2.0),
        })

        # Build router context (db/timeframe included)
        context: Dict[str, Any] = {
            "timeframe": timeframe,
            "db": db,
            "extra_context": extra_context or {},
            "kill_zone": kz_result,
            "smc": smc_result,
            "volume_profile": vp_result,
            "price_action": pa_result,
        }

        # Enhance signal using Adaptive Router (AI registry inference)
        enhanced_signal = await self.router.enhance_signal(
            base_signal=base_signal,
            symbol=symbol,
            timeframe=str(timeframe or "M15"),
            features=feats,
            context=context,
        )

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat(),
            "signal": enhanced_signal,
            "smc": smc_result,
            "volume_profile": vp_result,
            "price_action": pa_result,
            "kill_zone": kz_result,
            "features": dict(feats),
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
        Generate trading signal from all analyses (base score).
        """
        if not kz.get("can_trade", False):
            return {
                "action": "WAIT",
                "confidence": 0,
                "reason": "Outside optimal trading hours",
                "details": kz.get("reasons", [])
            }

        score = 0
        reasons = []

        # SMC Score
        bullish_obs = [
            ob for ob in smc.get("order_blocks", [])
            if ob.type.value == "bullish" and ob.strength in ["strong", "very_strong"]
        ]
        bearish_obs = [
            ob for ob in smc.get("order_blocks", [])
            if ob.type.value == "bearish" and ob.strength in ["strong", "very_strong"]
        ]

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

        action = self._action_from_score(score)
        confidence = min(100, abs(score))

        return {
            "action": action,
            "confidence": confidence,
            "score": score,
            "reasons": reasons,
            "entry_price": self.smc.data[-1]['close'] if self.smc.data else None,
            "suggested_sl": self._calculate_sl(action, smc),
            "suggested_tp": self._calculate_tp(action, smc),
            "kill_zone": kz,
            "adaptive": {
                "base_score": score,
            }
        }

    @staticmethod
    def _action_from_score(score: float) -> str:
        if score >= 60:
            return "STRONG_BUY"
        if score >= 40:
            return "BUY"
        if score <= -60:
            return "STRONG_SELL"
        if score <= -40:
            return "SELL"
        return "NEUTRAL"

    def _calculate_sl(self, action: str, smc: Dict) -> Optional[float]:
        """Calculate suggested stop loss"""
        if not self.smc or not self.smc.data:
            return None

        current_price = self.smc.data[-1]['close']

        if "BUY" in action:
            bullish_obs = [ob for ob in smc.get("order_blocks", []) if ob.type.value == "bullish"]
            if bullish_obs:
                return min(ob.low for ob in bullish_obs) - 5
            return current_price * 0.995

        bearish_obs = [ob for ob in smc.get("order_blocks", []) if ob.type.value == "bearish"]
        if bearish_obs:
            return max(ob.high for ob in bearish_obs) + 5
        return current_price * 1.005

    def _calculate_tp(self, action: str, smc: Dict) -> Optional[float]:
        """Calculate suggested take profit"""
        if not self.smc or not self.smc.data:
            return None

        current_price = self.smc.data[-1]['close']
        sl = self._calculate_sl(action, smc)
        if sl is None:
            return None

        risk = abs(current_price - sl)
        if "BUY" in action:
            return current_price + (risk * 2)
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
        (Note: Persistence/live execution upgrades are handled in the execution-focused patch,
               not required for stages 1.2/1.3)
        """
        action = signal.get("action", "NEUTRAL")
        if "NEUTRAL" in action or "WAIT" in action:
            return {"status": "skipped", "reason": "Neutral/Wait signal"}

        risk_assessment = self.risk_manager.assess_trade(
            balance=balance,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            current_positions=0
        )
        if not risk_assessment.can_trade:
            return {"status": "rejected", "reason": "Risk management", "details": risk_assessment.reasons}

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

        direction = "BUY" if "BUY" in action else "SELL"

        # Simulated by default in Vol-7
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
            await asyncio.sleep(1)

    def stop(self):
        """Stop trading engine"""
        self.is_running = False