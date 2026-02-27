"""
Integration Tests for API Endpoints
Testing authentication, trading, and data endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""
    
    def test_register_user(self, client: TestClient):
        """Test user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "password" not in data
    
    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "anotheruser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client: TestClient, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword"  # Assuming test user has this password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrong@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client: TestClient, test_user):
        """Test token refresh."""
        # First login to get refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "testpassword"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_logout(self, client: TestClient, auth_headers):
        """Test logout endpoint."""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


@pytest.mark.integration
class TestTradingEndpoints:
    """Test trading API endpoints."""
    
    def test_get_market_data(self, client: TestClient, auth_headers):
        """Test market data retrieval."""
        response = client.get(
            "/api/v1/market/data/EURUSD",
            headers=auth_headers,
            params={"timeframe": "H1", "limit": 100}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "candles" in data
        assert len(data["candles"]) <= 100
    
    def test_place_trade(self, client: TestClient, auth_headers):
        """Test placing a trade."""
        trade_data = {
            "symbol": "EURUSD",
            "side": "buy",
            "order_type": "market",
            "volume": 0.1,
            "stop_loss": 1.0800,
            "take_profit": 1.0900,
            "strategy": "SMC"
        }
        
        response = client.post(
            "/api/v1/trading/trades",
            headers=auth_headers,
            json=trade_data
        )
        
        assert response.status_code in [201, 400]  # 400 if market closed
        if response.status_code == 201:
            data = response.json()
            assert data["symbol"] == "EURUSD"
            assert data["side"] == "buy"
            assert "id" in data
    
    def test_get_positions(self, client: TestClient, auth_headers):
        """Test getting open positions."""
        response = client.get(
            "/api/v1/trading/positions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_close_position(self, client: TestClient, auth_headers):
        """Test closing a position."""
        # First get open positions
        positions = client.get(
            "/api/v1/trading/positions",
            headers=auth_headers
        ).json()
        
        if positions:
            position_id = positions[0]["id"]
            response = client.post(
                f"/api/v1/trading/positions/{position_id}/close",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "closed"
    
    def test_get_trade_history(self, client: TestClient, auth_headers):
        """Test trade history retrieval."""
        response = client.get(
            "/api/v1/trading/history",
            headers=auth_headers,
            params={"limit": 50, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "total" in data
        assert "page" in data
    
    def test_update_stop_loss(self, client: TestClient, auth_headers):
        """Test updating stop loss."""
        # Assuming there's an open position
        positions = client.get(
            "/api/v1/trading/positions",
            headers=auth_headers
        ).json()
        
        if positions:
            position_id = positions[0]["id"]
            response = client.patch(
                f"/api/v1/trading/positions/{position_id}",
                headers=auth_headers,
                json={"stop_loss": 1.0750}
            )
            
            assert response.status_code == 200


@pytest.mark.integration
class TestAIEndpoints:
    """Test AI-related API endpoints."""
    
    def test_get_ai_prediction(self, client: TestClient, auth_headers):
        """Test AI prediction endpoint."""
        response = client.get(
            "/api/v1/ai/predict/EURUSD",
            headers=auth_headers,
            params={"timeframe": "H1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "prediction" in data
        assert "confidence" in data
        assert "direction" in data["prediction"]
    
    def test_get_model_performance(self, client: TestClient, auth_headers):
        """Test model performance metrics."""
        response = client.get(
            "/api/v1/ai/models/performance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)
    
    def test_get_market_sentiment(self, client: TestClient, auth_headers):
        """Test market sentiment endpoint."""
        response = client.get(
            "/api/v1/ai/sentiment/EURUSD",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "sentiment_score" in data
        assert -1 <= data["sentiment_score"] <= 1


@pytest.mark.integration
class TestUserEndpoints:
    """Test user management endpoints."""
    
    def test_get_current_user(self, client: TestClient, auth_headers):
        """Test getting current user info."""
        response = client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data
        assert "id" in data
    
    def test_update_user_profile(self, client: TestClient, auth_headers):
        """Test updating user profile."""
        response = patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"full_name": "Updated Name"}
        )
        
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"
    
    def test_get_user_settings(self, client: TestClient, auth_headers):
        """Test getting user settings."""
        response = client.get(
            "/api/v1/users/me/settings",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_settings" in data
        assert "notification_settings" in data
    
    def test_update_trading_permissions(self, client: TestClient, admin_headers):
        """Test updating trading permissions (admin only)."""
        response = client.patch(
            "/api/v1/users/1/trading-permissions",
            headers=admin_headers,
            json={"trading_enabled": True, "max_lot_size": 5.0}
        )
        
        assert response.status_code == 200


@pytest.mark.integration
class TestDashboardEndpoints:
    """Test dashboard data endpoints."""
    
    def test_get_portfolio_summary(self, client: TestClient, auth_headers):
        """Test portfolio summary."""
        response = client.get(
            "/api/v1/dashboard/portfolio",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "equity" in data
        assert "open_positions" in data
        assert "today_pnl" in data
    
    def test_get_performance_metrics(self, client: TestClient, auth_headers):
        """Test performance metrics."""
        response = client.get(
            "/api/v1/dashboard/performance",
            headers=auth_headers,
            params={"period": "30d"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_return" in data
        assert "sharpe_ratio" in data
        assert "max_drawdown" in data
        assert "win_rate" in data
    
    def test_get_risk_metrics(self, client: TestClient, auth_headers):
        """Test risk metrics."""
        response = client.get(
            "/api/v1/dashboard/risk",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "current_exposure" in data
        assert "margin_level" in data
        assert "daily_var" in data


@pytest.mark.integration
class TestWebSocketAuth:
    """Test WebSocket authentication."""
    
    def test_websocket_connection(self, client: TestClient, auth_headers):
        """Test WebSocket connection with auth."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        with client.websocket_connect(
            f"/ws/v1/stream?token={token}"
        ) as websocket:
            # Test connection established
            websocket.send_json({"action": "subscribe", "channel": "trades"})
            data = websocket.receive_json()
            assert data["status"] == "subscribed"


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling."""
    
    def test_404_error(self, client: TestClient):
        """Test 404 error response."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_validation_error(self, client: TestClient, auth_headers):
        """Test validation error response."""
        response = client.post(
            "/api/v1/trading/trades",
            headers=auth_headers,
            json={"symbol": "INVALID"}  # Missing required fields
        )
        
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_unauthorized_access(self, client: TestClient):
        """Test unauthorized access."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()
    
    def test_forbidden_access(self, client: TestClient, auth_headers):
        """Test forbidden access (non-admin accessing admin endpoint)."""
        response = client.get(
            "/api/v1/admin/users",
            headers=auth_headers
        )
        
        assert response.status_code == 403
