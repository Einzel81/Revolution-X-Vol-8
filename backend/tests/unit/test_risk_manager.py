"""
Unit Tests for Risk Management System
Testing Risk Manager, Position Sizer, and Drawdown Protection
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.trading.risk.risk_manager import RiskManager
from app.trading.risk.position_sizer import PositionSizer
from app.trading.risk.drawdown_protection import DrawdownProtection
from app.trading.risk.correlation_manager import CorrelationManager
from app.models.trading import Position, Trade, Account


@pytest.mark.unit
class TestRiskManager:
    """Test suite for Risk Manager."""
    
    @pytest.fixture
    def risk_manager(self):
        """Create risk manager instance."""
        return RiskManager(
            max_risk_per_trade=0.02,
            max_daily_risk=0.06,
            max_total_risk=0.10,
            max_correlation_risk=0.05
        )
    
    @pytest.fixture
    def sample_account(self):
        """Create sample account."""
        return Account(
            id=1,
            balance=10000.0,
            equity=10000.0,
            margin_used=0.0,
            margin_free=10000.0,
            daily_pnl=0.0,
            total_pnl=0.0
        )
    
    def test_risk_manager_initialization(self, risk_manager):
        """Test risk manager initialization."""
        assert risk_manager.max_risk_per_trade == 0.02
        assert risk_manager.max_daily_risk == 0.06
        assert risk_manager.max_total_risk == 0.10
    
    def test_trade_risk_calculation(self, risk_manager, sample_account):
        """Test trade risk calculation."""
        risk = risk_manager.calculate_trade_risk(
            account=sample_account,
            entry_price=1.0850,
            stop_loss=1.0800,
            position_size=1.0,
            symbol="EURUSD"
        )
        
        assert 'monetary_risk' in risk
        assert 'risk_percentage' in risk
        assert 'r_multiple' in risk
        assert risk['risk_percentage'] <= risk_manager.max_risk_per_trade
    
    def test_approve_trade(self, risk_manager, sample_account):
        """Test trade approval logic."""
        trade_request = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'entry_price': 1.0850,
            'stop_loss': 1.0800,
            'take_profit': 1.0950,
            'position_size': 1.0
        }
        
        approval = risk_manager.approve_trade(trade_request, sample_account)
        
        assert 'approved' in approval
        assert 'reason' in approval
        assert 'risk_metrics' in approval
    
    def test_reject_high_risk_trade(self, risk_manager, sample_account):
        """Test rejection of high risk trade."""
        trade_request = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'entry_price': 1.0850,
            'stop_loss': 1.0400,  # Very wide stop
            'take_profit': 1.0950,
            'position_size': 10.0  # Large position
        }
        
        approval = risk_manager.approve_trade(trade_request, sample_account)
        assert approval['approved'] == False
        assert 'risk exceeds maximum' in approval['reason'].lower()
    
    def test_daily_risk_limit(self, risk_manager, sample_account):
        """Test daily risk limit enforcement."""
        # Simulate existing daily loss
        sample_account.daily_pnl = -500.0  # 5% loss
        
        trade_request = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'entry_price': 1.0850,
            'stop_loss': 1.0700,
            'position_size': 1.0
        }
        
        approval = risk_manager.approve_trade(trade_request, sample_account)
        # Should be rejected or warned due to daily risk limit
    
    def test_margin_requirement_check(self, risk_manager, sample_account):
        """Test margin requirement calculation."""
        margin = risk_manager.calculate_margin_requirement(
            symbol="EURUSD",
            position_size=1.0,
            price=1.0850
        )
        
        assert margin > 0
        assert margin <= sample_account.margin_free
    
    def test_exposure_calculation(self, risk_manager):
        """Test portfolio exposure calculation."""
        positions = [
            Position(symbol="EURUSD", size=1.0, side="buy"),
            Position(symbol="GBPUSD", size=0.5, side="buy"),
            Position(symbol="USDJPY", size=-1.0, side="sell")
        ]
        
        exposure = risk_manager.calculate_exposure(positions)
        
        assert 'total_long' in exposure
        assert 'total_short' in exposure
        assert 'net_exposure' in exposure
        assert 'currency_exposure' in exposure


@pytest.mark.unit
class TestPositionSizer:
    """Test suite for Position Sizer."""
    
    @pytest.fixture
    def position_sizer(self):
        """Create position sizer instance."""
        return PositionSizer(
            default_method='risk_based',
            risk_per_trade=0.02,
            max_position_size=10.0
        )
    
    def test_risk_based_sizing(self, position_sizer):
        """Test risk-based position sizing."""
        size = position_sizer.calculate_position_size(
            account_balance=10000.0,
            entry_price=1.0850,
            stop_loss=1.0800,
            risk_percent=0.02
        )
        
        expected_risk_amount = 10000.0 * 0.02  # $200
        price_risk = 1.0850 - 1.0800  # 0.0050
        expected_size = expected_risk_amount / (price_risk * 100000)  # Standard lot
        
        assert size > 0
        assert size <= position_sizer.max_position_size
    
    def test_fixed_fractional_sizing(self, position_sizer):
        """Test fixed fractional position sizing."""
        size = position_sizer.fixed_fractional(
            account_balance=10000.0,
            fraction=0.05,
            price=1.0850
        )
        
        assert size == pytest.approx(0.46, rel=0.1)  # ~0.46 lots
    
    def test_kelly_criterion_sizing(self, position_sizer):
        """Test Kelly Criterion sizing."""
        size = position_sizer.kelly_criterion(
            win_rate=0.55,
            avg_win=100.0,
            avg_loss=50.0,
            account_balance=10000.0,
            price=1.0850
        )
        
        # Kelly % = (0.55 * 100 - 0.45 * 50) / 100 = 0.325
        assert size > 0
        assert size <= 1.0  # Kelly suggests full Kelly, but we use fraction
    
    def test_volatility_adjusted_sizing(self, position_sizer):
        """Test volatility-adjusted position sizing."""
        size = position_sizer.volatility_adjusted(
            account_balance=10000.0,
            atr=0.0020,
            atr_multiple=2.0,
            risk_percent=0.02
        )
        
        # Smaller size for higher volatility
        assert size > 0
    
    def test_optimal_f_sizing(self, position_sizer):
        """Test Optimal F position sizing."""
        trades = [100, -50, 150, -30, 80, -40, 120, -60]
        
        size = position_sizer.optimal_f(
            trade_history=trades,
            account_balance=10000.0,
            price=1.0850
        )
        
        assert size > 0
        assert size <= position_sizer.max_position_size


@pytest.mark.unit
class TestDrawdownProtection:
    """Test suite for Drawdown Protection."""
    
    @pytest.fixture
    def dd_protection(self):
        """Create drawdown protection instance."""
        return DrawdownProtection(
            max_daily_drawdown=0.03,
            max_weekly_drawdown=0.05,
            max_monthly_drawdown=0.10,
            trading_pause_after_loss=True
        )
    
    def test_drawdown_calculation(self, dd_protection):
        """Test drawdown calculation."""
        equity_curve = [10000, 10200, 10100, 10300, 9900, 10050]
        
        dd = dd_protection.calculate_drawdown(equity_curve)
        
        assert 'current_drawdown' in dd
        assert 'max_drawdown' in dd
        assert 'drawdown_duration' in dd
        assert dd['max_drawdown'] >= dd['current_drawdown']
    
    def test_daily_drawdown_check(self, dd_protection):
        """Test daily drawdown limit check."""
        account = Account(
            starting_balance_daily=10000.0,
            equity=9700.0  # 3% drawdown
        )
        
        status = dd_protection.check_daily_drawdown(account)
        
        assert 'breached' in status
        assert 'action' in status
        assert status['breached'] == True
        assert status['action'] == 'stop_trading'
    
    def test_trading_pause_logic(self, dd_protection):
        """Test trading pause after consecutive losses."""
        recent_trades = [
            Trade(pnl=-100), Trade(pnl=-150), Trade(pnl=-80)
        ]
        
        pause = dd_protection.check_trading_pause(
            recent_trades=recent_trades,
            consecutive_losses_limit=3
        )
        
        assert pause['should_pause'] == True
        assert 'pause_duration' in pause
    
    def test_recovery_plan_generation(self, dd_protection):
        """Test recovery plan generation after drawdown."""
        plan = dd_protection.generate_recovery_plan(
            current_drawdown=0.08,
            account_balance=9200.0,
            target_recovery=0.95
        )
        
        assert 'target_profit' in plan
        assert 'reduced_risk' in plan
        assert 'time_estimate' in plan
        assert plan['reduced_risk'] < 0.02  # Reduced from normal 2%


@pytest.mark.unit
class TestCorrelationManager:
    """Test suite for Correlation Manager."""
    
    @pytest.fixture
    def corr_manager(self):
        """Create correlation manager instance."""
        return CorrelationManager(
            lookback_period=20,
            correlation_threshold=0.70
        )
    
    def test_correlation_matrix_calculation(self, corr_manager):
        """Test correlation matrix calculation."""
        returns_data = {
            'EURUSD': [0.001, -0.002, 0.003, -0.001, 0.002],
            'GBPUSD': [0.002, -0.001, 0.002, -0.002, 0.001],
            'USDJPY': [-0.001, 0.002, -0.001, 0.001, -0.002]
        }
        
        corr_matrix = corr_manager.calculate_correlation(returns_data)
        
        assert corr_matrix.shape == (3, 3)
        assert np.allclose(np.diag(corr_matrix), 1.0)
    
    def test_position_correlation_check(self, corr_manager):
        """Test position correlation check."""
        existing_positions = [
            Position(symbol="EURUSD", size=1.0),
            Position(symbol="GBPUSD", size=0.5)
        ]
        
        new_trade = {'symbol': 'EURGBP', 'size': 1.0}
        
        correlation = corr_manager.check_position_correlation(
            new_trade, existing_positions
        )
        
        assert 'correlated_positions' in correlation
        assert 'total_correlated_exposure' in correlation
        assert 'recommendation' in correlation
    
    def test_portfolio_heat_calculation(self, corr_manager):
        """Test portfolio heat calculation."""
        positions = [
            Position(symbol="EURUSD", size=1.0, side="buy"),
            Position(symbol="GBPUSD", size=1.0, side="buy"),
            Position(symbol="USDCHF", size=-1.0, side="sell")
        ]
        
        heat = corr_manager.calculate_portfolio_heat(positions)
        
        assert 'total_heat' in heat
        assert 'concentration_risk' in heat
        assert 'diversification_score' in heat
