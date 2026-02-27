"""
Unit Tests for Trading Strategies
Testing SMC, Volume Profile, and other strategies
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from app.trading.strategies.smc_strategy import SMCStrategy
from app.trading.strategies.volume_profile import VolumeProfileStrategy
from app.trading.strategies.ict_strategy import ICTStrategy
from app.trading.strategies.multi_timeframe import MultiTimeframeAnalysis


@pytest.mark.unit
@pytest.mark.trading
class TestSMCStrategy:
    """Test suite for Smart Money Concepts Strategy."""
    
    @pytest.fixture
    def smc_strategy(self):
        """Create SMC strategy instance."""
        return SMCStrategy(
            timeframe="H1",
            lookback_period=100,
            order_block_lookback=20,
            fvg_min_size=0.001
        )
    
    @pytest.fixture
    def market_structure_data(self):
        """Generate market structure data."""
        np.random.seed(42)
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")
        
        # Create trending market with clear structure
        trend = np.linspace(1.0800, 1.1000, 200)
        noise = np.random.randn(200) * 0.001
        
        data = pd.DataFrame({
            'open': trend + noise,
            'high': trend + noise + 0.002,
            'low': trend + noise - 0.002,
            'close': trend + noise + 0.001,
            'volume': np.random.randint(1000, 10000, 200)
        }, index=dates)
        return data
    
    def test_smc_initialization(self, smc_strategy):
        """Test SMC strategy initialization."""
        assert smc_strategy.timeframe == "H1"
        assert smc_strategy.lookback_period == 100
        assert smc_strategy.order_block_lookback == 20
    
    def test_market_structure_detection(self, smc_strategy, market_structure_data):
        """Test market structure detection."""
        structure = smc_strategy.detect_market_structure(market_structure_data)
        
        assert 'swing_highs' in structure
        assert 'swing_lows' in structure
        assert 'trend' in structure
        assert structure['trend'] in ['bullish', 'bearish', 'sideways']
    
    def test_order_block_detection(self, smc_strategy, market_structure_data):
        """Test Order Block detection."""
        obs = smc_strategy.detect_order_blocks(market_structure_data)
        
        assert isinstance(obs, list)
        for ob in obs:
            assert 'type' in ob  # bullish or bearish
            assert 'price' in ob
            assert 'volume' in ob
            assert 'strength' in ob
    
    def test_fair_value_gap_detection(self, smc_strategy, market_structure_data):
        """Test Fair Value Gap detection."""
        fvgs = smc_strategy.detect_fair_value_gaps(market_structure_data)
        
        assert isinstance(fvgs, list)
        for fvg in fvgs:
            assert 'type' in fvg  # bullish or bearish
            assert 'top' in fvg
            assert 'bottom' in fvg
            assert fvg['top'] > fvg['bottom']
    
    def test_liquidity_sweep_detection(self, smc_strategy, market_structure_data):
        """Test liquidity sweep detection."""
        sweeps = smc_strategy.detect_liquidity_sweeps(market_structure_data)
        
        assert isinstance(sweeps, list)
        for sweep in sweeps:
            assert 'type' in sweep  # buy_side or sell_side
            assert 'price' in sweep
            assert 'volume' in sweep
    
    def test_smc_signal_generation(self, smc_strategy, market_structure_data):
        """Test complete signal generation."""
        signal = smc_strategy.generate_signal(market_structure_data)
        
        assert 'action' in signal
        assert signal['action'] in ['buy', 'sell', 'hold']
        assert 'confidence' in signal
        assert 0 <= signal['confidence'] <= 1
        assert 'setup' in signal
        assert 'entry_price' in signal
        assert 'stop_loss' in signal
        assert 'take_profit' in signal
    
    def test_risk_reward_calculation(self, smc_strategy):
        """Test risk/reward calculation."""
        entry = 1.0850
        sl = 1.0800
        tp = 1.0950
        
        rr = smc_strategy.calculate_risk_reward(entry, sl, tp)
        assert rr == 2.0  # (1.0950 - 1.0850) / (1.0850 - 1.0800)
    
    def test_confluence_check(self, smc_strategy, market_structure_data):
        """Test confluence factors check."""
        confluence = smc_strategy.check_confluence(
            market_structure_data,
            order_block=True,
            fvg=True,
            liquidity_sweep=False
        )
        
        assert 'score' in confluence
        assert 0 <= confluence['score'] <= 1
        assert 'factors' in confluence


@pytest.mark.unit
@pytest.mark.trading
class TestVolumeProfileStrategy:
    """Test suite for Volume Profile Strategy."""
    
    @pytest.fixture
    def vp_strategy(self):
        """Create Volume Profile strategy instance."""
        return VolumeProfileStrategy(
            timeframe="H1",
            lookback_period=100,
            num_bins=24,
            value_area_pct=0.70
        )
    
    @pytest.fixture
    def volume_data(self):
        """Generate volume profile data."""
        np.random.seed(42)
        dates = pd.date_range(start="2024-01-01", periods=100, freq="H")
        
        # Create price with volume concentration
        base_price = 1.0850
        prices = base_price + np.random.randn(100) * 0.002
        
        # Higher volume around POC
        volumes = np.random.randint(1000, 5000, 100)
        mid_idx = 50
        volumes[mid_idx-10:mid_idx+10] *= 3
        
        data = pd.DataFrame({
            'open': prices - 0.001,
            'high': prices + 0.002,
            'low': prices - 0.002,
            'close': prices,
            'volume': volumes
        }, index=dates)
        return data
    
    def test_volume_profile_calculation(self, vp_strategy, volume_data):
        """Test volume profile histogram calculation."""
        profile = vp_strategy.calculate_volume_profile(volume_data)
        
        assert 'histogram' in profile
        assert 'price_levels' in profile
        assert 'poc' in profile  # Point of Control
        assert 'value_area_high' in profile
        assert 'value_area_low' in profile
        assert profile['value_area_high'] >= profile['value_area_low']
    
    def test_poc_identification(self, vp_strategy, volume_data):
        """Test Point of Control identification."""
        poc = vp_strategy.find_poc(volume_data)
        
        assert 'price' in poc
        assert 'volume' in poc
        assert poc['volume'] == volume_data['volume'].max()
    
    def test_value_area_calculation(self, vp_strategy, volume_data):
        """Test Value Area calculation."""
        va = vp_strategy.calculate_value_area(volume_data, percentile=0.70)
        
        assert 'high' in va
        assert 'low' in va
        assert 'volume' in va
        assert va['high'] > va['low']
    
    def test_volume_nodes_detection(self, vp_strategy, volume_data):
        """Test volume nodes detection."""
        nodes = vp_strategy.detect_volume_nodes(volume_data)
        
        assert isinstance(nodes, list)
        for node in nodes:
            assert 'type' in node  # high_volume or low_volume
            assert 'price' in node
            assert 'volume' in node
    
    def test_vp_signal_generation(self, vp_strategy, volume_data):
        """Test signal generation based on volume profile."""
        signal = vp_strategy.generate_signal(volume_data)
        
        assert 'action' in signal
        assert 'confidence' in signal
        assert 'poc_distance' in signal
        assert 'in_value_area' in signal
    
    def test_volume_imbalance_detection(self, vp_strategy, volume_data):
        """Test volume imbalance detection."""
        imbalance = vp_strategy.detect_volume_imbalance(volume_data)
        
        assert 'buy_volume' in imbalance
        assert 'sell_volume' in imbalance
        assert 'imbalance_ratio' in imbalance
        assert imbalance['imbalance_ratio'] >= 0


@pytest.mark.unit
@pytest.mark.trading
class TestICTStrategy:
    """Test suite for ICT (Inner Circle Trader) Strategy."""
    
    @pytest.fixture
    def ict_strategy(self):
        """Create ICT strategy instance."""
        return ICTStrategy(
            timeframe="H1",
            killzone_times=["08:30", "14:00"],
            use_fvg=True,
            use_ob=True
        )
    
    def test_killzone_detection(self, ict_strategy):
        """Test killzone time detection."""
        import pytz
        from datetime import datetime
        
        # London killzone (08:30)
        time_london = datetime(2024, 1, 1, 8, 30, tzinfo=pytz.UTC)
        assert ict_strategy.is_killzone(time_london) == True
        
        # NY killzone (14:00)
        time_ny = datetime(2024, 1, 1, 14, 0, tzinfo=pytz.UTC)
        assert ict_strategy.is_killzone(time_ny) == True
        
        # Outside killzone
        time_other = datetime(2024, 1, 1, 20, 0, tzinfo=pytz.UTC)
        assert ict_strategy.is_killzone(time_other) == False
    
    def test_ict_concepts_integration(self, ict_strategy, market_structure_data):
        """Test ICT concepts integration."""
        concepts = ict_strategy.analyze_ict_concepts(market_structure_data)
        
        assert 'premium_discount' in concepts
        assert 'market_structure' in concepts
        assert 'order_flow' in concepts
    
    def test_liquidity_void_detection(self, ict_strategy, market_structure_data):
        """Test liquidity void detection."""
        voids = ict_strategy.detect_liquidity_voids(market_structure_data)
        
        assert isinstance(voids, list)
        for void in voids:
            assert 'start' in void
            assert 'end' in void
            assert 'type' in void


@pytest.mark.unit
@pytest.mark.trading
class TestMultiTimeframeAnalysis:
    """Test suite for Multi-Timeframe Analysis."""
    
    @pytest.fixture
    def mtf_analyzer(self):
        """Create MTF analyzer instance."""
        return MultiTimeframeAnalysis(
            timeframes=["M15", "H1", "H4", "D1"],
            primary_timeframe="H1"
        )
    
    def test_timeframe_alignment(self, mtf_analyzer):
        """Test timeframe alignment check."""
        alignment = mtf_analyzer.check_alignment(
            m15_signal='buy',
            h1_signal='buy',
            h4_signal='buy',
            d1_signal='sell'
        )
        
        assert 'score' in alignment
        assert 'direction' in alignment
        assert 'agreement' in alignment
        assert 0 <= alignment['score'] <= 1
    
    def test_trend_consistency(self, mtf_analyzer):
        """Test trend consistency across timeframes."""
        trends = {
            'M15': 'bullish',
            'H1': 'bullish',
            'H4': 'bullish',
            'D1': 'bearish'
        }
        
        consistency = mtf_analyzer.check_trend_consistency(trends)
        assert consistency['score'] == 0.75  # 3 out of 4 agree
        assert consistency['dominant_trend'] == 'bullish'
    
    def test_mtf_signal_aggregation(self, mtf_analyzer):
        """Test signal aggregation from multiple timeframes."""
        signals = {
            'M15': {'action': 'buy', 'confidence': 0.8},
            'H1': {'action': 'buy', 'confidence': 0.9},
            'H4': {'action': 'hold', 'confidence': 0.5},
            'D1': {'action': 'sell', 'confidence': 0.7}
        }
        
        aggregated = mtf_analyzer.aggregate_signals(signals)
        
        assert 'final_action' in aggregated
        assert 'confidence' in aggregated
        assert 'timeframe_weights' in aggregated
    
    def test_higher_timeframe_bias(self, mtf_analyzer):
        """Test higher timeframe bias calculation."""
        htf_data = {
            'trend': 'bullish',
            'key_level': 1.0800,
            'structure': 'uptrend'
        }
        
        bias = mtf_analyzer.calculate_htf_bias(htf_data, "H4")
        assert bias['direction'] == 'bullish'
        assert 'strength' in bias
        assert 'key_levels' in bias
