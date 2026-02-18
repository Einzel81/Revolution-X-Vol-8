"""
Unit Tests for AI Models
Testing LSTM, XGBoost, LightGBM models
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import torch

from app.ai.models.lstm_model import LSTMModel, LSTMPredictor
from app.ai.models.xgboost_model import XGBoostPredictor
from app.ai.models.lightgbm_model import LightGBMPredictor
from app.ai.features.technical_indicators import TechnicalIndicators


@pytest.mark.unit
@pytest.mark.ai
class TestLSTMModel:
    """Test suite for LSTM Model."""
    
    def test_lstm_model_initialization(self):
        """Test LSTM model initialization."""
        model = LSTMModel(
            input_size=20,
            hidden_size=128,
            num_layers=2,
            output_size=3,
            dropout=0.2
        )
        assert model.hidden_size == 128
        assert model.num_layers == 2
        assert model.input_size == 20
    
    def test_lstm_forward_pass(self):
        """Test LSTM forward pass."""
        model = LSTMModel(input_size=10, hidden_size=64, num_layers=1, output_size=1)
        batch_size = 32
        seq_length = 50
        x = torch.randn(batch_size, seq_length, 10)
        
        output = model(x)
        assert output.shape == (batch_size, 1)
    
    def test_lstm_predictor_initialization(self):
        """Test LSTM predictor initialization."""
        predictor = LSTMPredictor(
            model_path="models/lstm_test.pth",
            sequence_length=60,
            n_features=20
        )
        assert predictor.sequence_length == 60
        assert predictor.n_features == 20
    
    @patch('torch.load')
    @patch('app.ai.models.lstm_model.LSTMModel')
    def test_lstm_prediction(self, mock_model_class, mock_load):
        """Test LSTM prediction."""
        # Mock model
        mock_model = MagicMock()
        mock_model.return_value = torch.randn(1, 3)
        mock_model.eval.return_value = None
        mock_model_class.return_value = mock_model
        mock_load.return_value = {'model_state_dict': {}}
        
        predictor = LSTMPredictor()
        
        # Create sample data
        data = pd.DataFrame({
            'close': np.random.randn(100),
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        with patch.object(predictor, 'model', mock_model):
            prediction = predictor.predict(data)
            assert 'direction' in prediction
            assert 'confidence' in prediction
            assert 'probabilities' in prediction


@pytest.mark.unit
@pytest.mark.ai
class TestXGBoostModel:
    """Test suite for XGBoost Model."""
    
    @patch('xgboost.XGBClassifier')
    def test_xgboost_initialization(self, mock_xgb):
        """Test XGBoost predictor initialization."""
        mock_model = MagicMock()
        mock_xgb.return_value = mock_model
        
        predictor = XGBoostPredictor(model_path="models/xgb_test.json")
        assert predictor.model_path == "models/xgb_test.json"
    
    @patch('xgboost.XGBClassifier')
    def test_xgboost_prediction(self, mock_xgb):
        """Test XGBoost prediction."""
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.2, 0.5, 0.3]])
        mock_model.predict.return_value = np.array([1])
        mock_xgb.return_value = mock_model
        
        predictor = XGBoostPredictor()
        predictor.model = mock_model
        
        features = pd.DataFrame({
            'rsi': [50],
            'macd': [0.5],
            'bb_position': [0.3]
        })
        
        prediction = predictor.predict(features)
        assert prediction['direction'] in ['buy', 'sell', 'neutral']
        assert 0 <= prediction['confidence'] <= 1
    
    def test_feature_importance(self):
        """Test feature importance extraction."""
        mock_model = MagicMock()
        mock_model.feature_importances_ = np.array([0.3, 0.5, 0.2])
        
        predictor = XGBoostPredictor()
        predictor.model = mock_model
        predictor.feature_names = ['rsi', 'macd', 'bb_position']
        
        importance = predictor.get_feature_importance()
        assert len(importance) == 3
        assert importance[0]['feature'] == 'macd'
        assert importance[0]['importance'] == 0.5


@pytest.mark.unit
@pytest.mark.ai
class TestLightGBMModel:
    """Test suite for LightGBM Model."""
    
    @patch('lightgbm.Booster')
    def test_lightgbm_initialization(self, mock_lgb):
        """Test LightGBM predictor initialization."""
        mock_model = MagicMock()
        mock_lgb.return_value = mock_model
        
        predictor = LightGBMPredictor(model_path="models/lgb_test.txt")
        assert predictor.model_path == "models/lgb_test.txt"
    
    @patch('lightgbm.Booster')
    def test_lightgbm_prediction(self, mock_lgb):
        """Test LightGBM prediction."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([[0.1, 0.7, 0.2]])
        mock_lgb.return_value = mock_model
        
        predictor = LightGBMPredictor()
        predictor.model = mock_model
        
        features = np.array([[50, 0.5, 0.3]])
        prediction = predictor.predict(features)
        
        assert 'direction' in prediction
        assert 'confidence' in prediction


@pytest.mark.unit
@pytest.mark.ai
class TestTechnicalIndicators:
    """Test suite for Technical Indicators."""
    
    @pytest.fixture
    def sample_ohlcv(self):
        """Generate sample OHLCV data."""
        np.random.seed(42)
        dates = pd.date_range(start="2024-01-01", periods=100, freq="H")
        data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 101,
            'low': np.random.randn(100).cumsum() + 99,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        return data
    
    def test_rsi_calculation(self, sample_ohlcv):
        """Test RSI calculation."""
        ti = TechnicalIndicators()
        rsi = ti.calculate_rsi(sample_ohlcv['close'], period=14)
        
        assert len(rsi) == len(sample_ohlcv)
        assert rsi.min() >= 0
        assert rsi.max() <= 100
        assert not rsi.isna().all()
    
    def test_macd_calculation(self, sample_ohlcv):
        """Test MACD calculation."""
        ti = TechnicalIndicators()
        macd, signal, histogram = ti.calculate_macd(sample_ohlcv['close'])
        
        assert len(macd) == len(sample_ohlcv)
        assert len(signal) == len(sample_ohlcv)
        assert len(histogram) == len(sample_ohlcv)
    
    def test_bollinger_bands(self, sample_ohlcv):
        """Test Bollinger Bands calculation."""
        ti = TechnicalIndicators()
        upper, middle, lower = ti.calculate_bollinger_bands(sample_ohlcv['close'])
        
        assert len(upper) == len(sample_ohlcv)
        assert (upper >= middle).all()
        assert (middle >= lower).all()
    
    def test_atr_calculation(self, sample_ohlcv):
        """Test ATR calculation."""
        ti = TechnicalIndicators()
        atr = ti.calculate_atr(
            sample_ohlcv['high'],
            sample_ohlcv['low'],
            sample_ohlcv['close']
        )
        
        assert len(atr) == len(sample_ohlcv)
        assert (atr >= 0).all()
    
    def test_feature_generation(self, sample_ohlcv):
        """Test complete feature generation."""
        ti = TechnicalIndicators()
        features = ti.generate_all_features(sample_ohlcv)
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) == len(sample_ohlcv)
        assert 'rsi' in features.columns
        assert 'macd' in features.columns
        assert 'bb_upper' in features.columns
        assert 'atr' in features.columns


@pytest.mark.unit
@pytest.mark.ai
class TestEnsembleModel:
    """Test suite for Ensemble Model."""
    
    @patch('app.ai.models.lstm_model.LSTMPredictor')
    @patch('app.ai.models.xgboost_model.XGBoostPredictor')
    @patch('app.ai.models.lightgbm_model.LightGBMPredictor')
    def test_ensemble_prediction(self, mock_lgb, mock_xgb, mock_lstm):
        """Test ensemble prediction aggregation."""
        from app.ai.models.ensemble import EnsemblePredictor
        
        # Mock predictions
        mock_lstm.return_value.predict.return_value = {
            'direction': 'buy',
            'confidence': 0.8,
            'probabilities': [0.1, 0.8, 0.1]
        }
        mock_xgb.return_value.predict.return_value = {
            'direction': 'buy',
            'confidence': 0.75,
            'probabilities': [0.15, 0.75, 0.1]
        }
        mock_lgb.return_value.predict.return_value = {
            'direction': 'sell',
            'confidence': 0.6,
            'probabilities': [0.6, 0.3, 0.1]
        }
        
        ensemble = EnsemblePredictor()
        result = ensemble.predict(mock_market_data())
        
        assert 'final_prediction' in result
        assert 'model_agreement' in result
        assert 'weighted_confidence' in result
