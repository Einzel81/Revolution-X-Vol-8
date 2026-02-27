"""
Smart Opportunity Scanner
Multi-asset scanning with AI scoring
Revolution X - AI System
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from .ensemble import EnsembleFusion, EnsemblePrediction

logger = logging.getLogger(__name__)

@dataclass
class OpportunityScore:
    symbol: str
    name: str
    current_price: float
    daily_change: float
    ai_score: float  # 0-100
    trend_score: float
    momentum_score: float
    volume_score: float
    smc_score: float
    risk_level: str
    recommended_action: str
    confidence: float
    last_update: datetime = field(default_factory=datetime.now)

class SmartOpportunityScanner:
    """
    Scans multiple precious metals assets for best trading opportunities
    """
    
    ASSETS = {
        'XAUUSD': {'name': 'Gold', 'type': 'metal', 'weight': 1.0},
        'XAGUSD': {'name': 'Silver', 'type': 'metal', 'weight': 0.8},
        'XPTUSD': {'name': 'Platinum', 'type': 'metal', 'weight': 0.6},
        'XPDUSD': {'name': 'Palladium', 'type': 'metal', 'weight': 0.6},
        'COPPER': {'name': 'Copper', 'type': 'metal', 'weight': 0.5}
    }
    
    def __init__(self, 
                 ensemble: Optional[EnsembleFusion] = None,
                 min_score_threshold: float = 60.0,
                 auto_select: bool = False):
        self.ensemble = ensemble or EnsembleFusion()
        self.min_score_threshold = min_score_threshold
        self.auto_select = auto_select
        self.opportunities: Dict[str, OpportunityScore] = {}
        self.scan_history: List[Dict] = []
        
    async def scan_all_assets(self, 
                             data_fetcher,
                             smc_analyzer=None,
                             volume_analyzer=None) -> List[OpportunityScore]:
        """Scan all configured assets"""
        tasks = []
        
        for symbol, config in self.ASSETS.items():
            task = self._analyze_asset(
                symbol, 
                config,
                data_fetcher,
                smc_analyzer,
                volume_analyzer
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        opportunities = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scan error: {result}")
                continue
            if result and result.ai_score >= self.min_score_threshold:
                opportunities.append(result)
        
        # Sort by score
        opportunities.sort(key=lambda x: x.ai_score, reverse=True)
        
        # Store
        for opp in opportunities:
            self.opportunities[opp.symbol] = opp
        
        # Log scan
        self.scan_history.append({
            'timestamp': datetime.now(),
            'assets_scanned': len(self.ASSETS),
            'opportunities_found': len(opportunities),
            'top_pick': opportunities[0].symbol if opportunities else None
        })
        
        return opportunities
    
    async def _analyze_asset(self,
                            symbol: str,
                            config: Dict,
                            data_fetcher,
                            smc_analyzer,
                            volume_analyzer) -> Optional[OpportunityScore]:
        """Analyze single asset"""
        try:
            # Fetch data
            df = await data_fetcher(symbol, timeframe='1h', limit=500)
            if df is None or len(df) < 100:
                return None
            
            current_price = df['close'].iloc[-1]
            daily_change = (current_price / df['close'].iloc[-24] - 1) * 100 if len(df) >= 24 else 0
            
            # Get SMC analysis
            smc_data = None
            if smc_analyzer:
                smc_data = smc_analyzer.analyze(df)
            
            # Get Volume Profile
            vp_data = None
            if volume_analyzer:
                vp_data = volume_analyzer.calculate_profile(df)
            
            # Get AI predictions
            lstm_pred = self.ensemble.lstm.predict(df)
            xgb_pred = self.ensemble.xgboost.predict(df, smc_data, vp_data)
            lgb_pred = self.ensemble.lightgbm.predict(df, xgb_pred.signal)
            
            # Fuse predictions
            ensemble_pred = self.ensemble.fuse_predictions(lstm_pred, xgb_pred, lgb_pred)
            
            # Calculate component scores
            trend_score = self._calculate_trend_score(df)
            momentum_score = self._calculate_momentum_score(df)
            volume_score = self._calculate_volume_score(df)
            smc_score = self._calculate_smc_score(smc_data) if smc_data else 50
            
            # Calculate final AI score
            base_score = ensemble_pred.confidence * 100
            
            # Adjust based on components
            ai_score = (
                base_score * 0.4 +
                trend_score * 0.2 +
                momentum_score * 0.2 +
                volume_score * 0.1 +
                smc_score * 0.1
            ) * config['weight']
            
            # Cap at 100
            ai_score = min(100, max(0, ai_score))
            
            # Determine action
            if ensemble_pred.signal_strength.value in ['strong_buy', 'buy']:
                action = 'BUY'
            elif ensemble_pred.signal_strength.value in ['strong_sell', 'sell']:
                action = 'SELL'
            else:
                action = 'HOLD'
            
            return OpportunityScore(
                symbol=symbol,
                name=config['name'],
                current_price=round(current_price, 2),
                daily_change=round(daily_change, 2),
                ai_score=round(ai_score, 1),
                trend_score=round(trend_score, 1),
                momentum_score=round(momentum_score, 1),
                volume_score=round(volume_score, 1),
                smc_score=round(smc_score, 1),
                risk_level=ensemble_pred.risk_level,
                recommended_action=action,
                confidence=round(ensemble_pred.confidence, 3)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_trend_score(self, df: pd.DataFrame) -> float:
        """Calculate trend strength score 0-100"""
        # Multiple timeframe trend alignment
        scores = []
        
        # Short term
        ema_10 = df['close'].ewm(span=10).mean().iloc[-1]
        ema_20 = df['close'].ewm(span=20).mean().iloc[-1]
        short_trend = 100 if df['close'].iloc[-1] > ema_10 > ema_20 else 0
        
        # Medium term
        ema_50 = df['close'].ewm(span=50).mean().iloc[-1]
        medium_trend = 100 if df['close'].iloc[-1] > ema_50 else 0
        
        # ADX for trend strength
        adx = self._calculate_adx(df)
        trend_strength = min(100, adx * 10)
        
        return (short_trend + medium_trend + trend_strength) / 3
    
    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """Calculate momentum score"""
        # RSI
        rsi = self._calculate_rsi(df['close'])
        current_rsi = rsi.iloc[-1]
        
        # Normalize RSI to 0-100 (50 is neutral)
        if current_rsi > 50:
            momentum = (current_rsi - 50) * 2
        else:
            momentum = (50 - current_rsi) * 2
        
        # MACD momentum
        macd_line, signal_line = self._calculate_macd(df['close'])
        macd_momentum = 100 if macd_line.iloc[-1] > signal_line.iloc[-1] else 0
        
        return (momentum + macd_momentum) / 2
    
    def _calculate_volume_score(self, df: pd.DataFrame) -> float:
        """Calculate volume confirmation score"""
        vol_ma = df['volume'].rolling(20).mean()
        current_vol = df['volume'].iloc[-1]
        
        # Volume trend
        vol_ratio = current_vol / vol_ma.iloc[-1]
        
        # Price-volume correlation
        price_change = df['close'].pct_change()
        vol_change = df['volume'].pct_change()
        correlation = price_change.corr(vol_change)
        
        if pd.isna(correlation):
            correlation = 0
        
        # High volume with price movement is good
        if vol_ratio > 1.5 and abs(price_change.iloc[-1]) > 0.001:
            return 80 + min(20, vol_ratio * 10)
        
        return 50 + (correlation * 50)
    
    def _calculate_smc_score(self, smc_data: Dict) -> float:
        """Calculate SMC quality score"""
        score = 50
        
        if smc_data.get('order_block_strength', 0) > 0.7:
            score += 20
        if smc_data.get('fair_value_gap', False):
            score += 15
        if smc_data.get('liquidity_sweep', False):
            score += 15
        
        return min(100, score)
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ADX"""
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff().abs()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift()).abs(),
            (df['low'] - df['close'].shift()).abs()
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 25
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: pd.Series):
        """Calculate MACD"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        return macd_line, signal_line
    
    def get_top_opportunities(self, n: int = 3) -> List[OpportunityScore]:
        """Get top N opportunities"""
        sorted_opps = sorted(
            self.opportunities.values(),
            key=lambda x: x.ai_score,
            reverse=True
        )
        return sorted_opps[:n]
    
    def get_auto_selected_trade(self) -> Optional[OpportunityScore]:
        """Auto-select best opportunity if auto mode enabled"""
        if not self.auto_select or not self.opportunities:
            return None
        
        best = max(self.opportunities.values(), key=lambda x: x.ai_score)
        
        if best.ai_score >= self.min_score_threshold and best.confidence > 0.7:
            return best
        
        return None
