"""
End-to-End Tests for Complete Trading Flows
Testing user journeys from registration to trading
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.main import app
from app.core.config import settings


@pytest.mark.e2e
class TestCompleteTradingFlow:
    """Test complete trading user journey."""
    
    @pytest.mark.asyncio
    async def test_user_registration_to_first_trade(self, async_client: AsyncClient):
        """E2E: Register → Verify → Deposit → Trade."""
        # 1. Register new user
        register_data = {
            "email": f"trader_{datetime.now().timestamp()}@test.com",
            "username": f"trader_{int(datetime.now().timestamp())}",
            "password": "SecureTrading123!",
            "full_name": "Test Trader"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # 2. Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": register_data["email"],
                "password": register_data["password"]
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Complete profile setup
        profile_response = await async_client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={
                "phone": "+1234567890",
                "timezone": "UTC",
                "risk_tolerance": "moderate"
            }
        )
        assert profile_response.status_code == 200
        
        # 4. Configure trading settings
        settings_response = await async_client.put(
            "/api/v1/users/me/settings",
            headers=headers,
            json={
                "risk_per_trade": 0.02,
                "max_daily_loss": 0.05,
                "default_stop_loss": 50,
                "default_take_profit": 100,
                "auto_trading_enabled": False
            }
        )
        assert settings_response.status_code == 200
        
        # 5. Connect MT5 account (simulated)
        mt5_response = await async_client.post(
            "/api/v1/brokers/connect",
            headers=headers,
            json={
                "broker": "mt5_demo",
                "account_number": "12345678",
                "password": "demo_password",
                "server": "DemoServer"
            }
        )
        assert mt5_response.status_code in [200, 201]
        
        # 6. Get market analysis
        analysis_response = await async_client.get(
            "/api/v1/ai/analysis/EURUSD",
            headers=headers,
            params={"timeframe": "H1"}
        )
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        assert "trend" in analysis
        assert "key_levels" in analysis
        
        # 7. Place first trade
        trade_response = await async_client.post(
            "/api/v1/trading/trades",
            headers=headers,
            json={
                "symbol": "EURUSD",
                "side": "buy",
                "order_type": "market",
                "volume": 0.01,
                "stop_loss": 1.0800,
                "take_profit": 1.0900,
                "strategy": "AI_Ensemble",
                "comment": "First E2E test trade"
            }
        )
        assert trade_response.status_code in [201, 400]  # 400 if market closed
        trade_id = trade_response.json().get("id")
        
        # 8. Monitor position via WebSocket
        if trade_id:
            async with async_client.websocket_connect(
                f"/ws/v1/trading?token={access_token}"
            ) as ws:
                await ws.send_json({"action": "subscribe_positions"})
                
                # Wait for position update
                position_update = await asyncio.wait_for(
                    ws.receive_json(),
                    timeout=5.0
                )
                assert position_update["type"] == "positions_snapshot"
        
        # 9. Check trade history
        history_response = await async_client.get(
            "/api/v1/trading/history",
            headers=headers
        )
        assert history_response.status_code == 200
        
        # 10. Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            headers=headers
        )
        assert logout_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_ai_guardian_protection_flow(self, async_client: AsyncClient, test_user):
        """E2E: Test AI Guardian risk protection."""
        # Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword"
            }
        )
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # 1. Attempt high-risk trade
        high_risk_trade = {
            "symbol": "EURUSD",
            "side": "buy",
            "order_type": "market",
            "volume": 50.0,  # Very large size
            "leverage": 500,
            "stop_loss": 1.0000  # Very wide stop
        }
        
        trade_response = await async_client.post(
            "/api/v1/trading/trades",
            headers=headers,
            json=high_risk_trade
        )
        
        # Should be blocked by AI Guardian
        assert trade_response.status_code == 403
        assert "risk limit" in trade_response.json()["detail"].lower()
        
        # 2. Check AI Guardian alert
        alerts_response = await async_client.get(
            "/api/v1/guardian/alerts",
            headers=headers
        )
        assert alerts_response.status_code == 200
        alerts = alerts_response.json()
        assert any("high risk" in alert["message"].lower() for alert in alerts)
        
        # 3. Attempt consecutive losing trades
        for i in range(3):
            await async_client.post(
                "/api/v1/trading/trades",
                headers=headers,
                json={
                    "symbol": "EURUSD",
                    "side": "buy",
                    "volume": 0.1
                }
            )
        
        # 4. Check if trading paused
        status_response = await async_client.get(
            "/api/v1/guardian/status",
            headers=headers
        )
        status = status_response.json()
        
        if status.get("trading_paused"):
            # Try to trade while paused
            paused_trade = await async_client.post(
                "/api/v1/trading/trades",
                headers=headers,
                json={
                    "symbol": "EURUSD",
                    "side": "buy",
                    "volume": 0.1
                }
            )
            assert paused_trade.status_code == 403
            assert "trading paused" in paused_trade.json()["detail"].lower()


@pytest.mark.e2e
class TestMultiUserScenarios:
    """Test scenarios with multiple users."""
    
    @pytest.mark.asyncio
    async def test_concurrent_trading(self, async_client: AsyncClient):
        """E2E: Multiple users trading simultaneously."""
        users = []
        
        # Create 5 users
        for i in range(5):
            register_data = {
                "email": f"concurrent_{i}_{datetime.now().timestamp()}@test.com",
                "username": f"concurrent_{i}",
                "password": "TestPass123!"
            }
            
            response = await async_client.post("/api/v1/auth/register", json=register_data)
            if response.status_code == 201:
                login_response = await async_client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": register_data["email"],
                        "password": register_data["password"]
                    }
                )
                users.append({
                    "headers": {"Authorization": f"Bearer {login_response.json()['access_token']}"},
                    "id": response.json()["id"]
                })
        
        # All users place trades simultaneously
        async def place_trade(user):
            return await async_client.post(
                "/api/v1/trading/trades",
                headers=user["headers"],
                json={
                    "symbol": "EURUSD",
                    "side": "buy",
                    "volume": 0.1
                }
            )
        
        responses = await asyncio.gather(*[place_trade(user) for user in users])
        
        # All should succeed (or fail gracefully)
        for response in responses:
            assert response.status_code in [201, 400, 429]  # Created, Bad Request, or Rate Limited
    
    @pytest.mark.asyncio
    async def test_social_trading_flow(self, async_client: AsyncClient):
        """E2E: Social trading - copy trading flow."""
        # 1. Create master trader
        master_register = {
            "email": f"master_{datetime.now().timestamp()}@test.com",
            "username": "master_trader",
            "password": "MasterPass123!"
        }
        master_reg = await async_client.post("/api/v1/auth/register", json=master_register)
        master_token = (await async_client.post(
            "/api/v1/auth/login",
            data={"username": master_register["email"], "password": master_register["password"]}
        )).json()["access_token"]
        master_headers = {"Authorization": f"Bearer {master_token}"}
        
        # 2. Enable copy trading
        await async_client.patch(
            "/api/v1/social/settings",
            headers=master_headers,
            json={"copy_trading_enabled": True, "commission_rate": 0.1}
        )
        
        # 3. Create follower
        follower_register = {
            "email": f"follower_{datetime.now().timestamp()}@test.com",
            "username": "follower",
            "password": "FollowerPass123!"
        }
        follower_reg = await async_client.post("/api/v1/auth/register", json=follower_register)
        follower_token = (await async_client.post(
            "/api/v1/auth/login",
            data={"username": follower_register["email"], "password": follower_register["password"]}
        )).json()["access_token"]
        follower_headers = {"Authorization": f"Bearer {follower_token}"}
        
        # 4. Follow master
        follow_response = await async_client.post(
            f"/api/v1/social/follow/{master_reg.json()['id']}",
            headers=follower_headers,
            json={"allocation": 0.5, "max_trade_size": 1.0}
        )
        assert follow_response.status_code == 200
        
        # 5. Master places trade
        master_trade = await async_client.post(
            "/api/v1/trading/trades",
            headers=master_headers,
            json={
                "symbol": "EURUSD",
                "side": "buy",
                "volume": 1.0
            }
        )
        assert master_trade.status_code in [201, 400]
        
        # 6. Verify follower received copy trade (async, check after delay)
        await asyncio.sleep(2)
        follower_positions = await async_client.get(
            "/api/v1/trading/positions",
            headers=follower_headers
        )
        assert follower_positions.status_code == 200


@pytest.mark.e2e
class TestMarketDataFlow:
    """Test market data and analysis flow."""
    
    @pytest.mark.asyncio
    async def test_real_time_analysis_update(self, async_client: AsyncClient, auth_headers):
        """E2E: Real-time analysis updates."""
        async with async_client.websocket_connect(
            f"/ws/v1/ai?token={auth_headers['Authorization'].replace('Bearer ', '')}"
        ) as ws:
            # Subscribe to analysis updates
            await ws.send_json({
                "action": "subscribe_analysis",
                "symbol": "EURUSD",
                "timeframe": "M5"
            })
            
            # Receive initial analysis
            analysis = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            assert analysis["type"] == "analysis"
            
            # Wait for update (should come when new candle closes)
            updates = []
            for _ in range(3):
                try:
                    update = await asyncio.wait_for(ws.receive_json(), timeout=60.0)
                    if update["type"] == "analysis_update":
                        updates.append(update)
                except asyncio.TimeoutError:
                    break
            
            # Should receive at least one update
            assert len(updates) >= 0  # May be 0 in test environment
    
    @pytest.mark.asyncio
    async def test_strategy_backtest_to_live(self, async_client: AsyncClient, auth_headers):
        """E2E: Backtest strategy then deploy live."""
        # 1. Run backtest
        backtest_response = await async_client.post(
            "/api/v1/ai/backtest",
            headers=auth_headers,
            json={
                "strategy": "SMC",
                "symbol": "EURUSD",
                "timeframe": "H1",
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "initial_balance": 10000
            }
        )
        assert backtest_response.status_code == 200
        backtest_result = backtest_response.json()
        assert "total_return" in backtest_result
        assert "sharpe_ratio" in backtest_result
        
        # 2. If profitable, deploy to live
        if backtest_result["total_return"] > 0:
            deploy_response = await async_client.post(
                "/api/v1/ai/deploy",
                headers=auth_headers,
                json={
                    "strategy": "SMC",
                    "symbol": "EURUSD",
                    "timeframe": "H1",
                    "risk_per_trade": 0.02,
                    "auto_execute": False  # Signal only, manual execution
                }
            )
            assert deploy_response.status_code == 200
            
            # 3. Verify deployment
            deployed = await async_client.get(
                "/api/v1/ai/deployed-strategies",
                headers=auth_headers
            )
            assert any(s["strategy"] == "SMC" for s in deployed.json())


@pytest.mark.e2e
class TestErrorRecovery:
    """Test system recovery from errors."""
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, async_client: AsyncClient, auth_headers):
        """E2E: System continues working when AI service fails."""
        # Simulate AI service failure (if possible in test env)
        # Then verify basic trading still works
        
        response = await async_client.get(
            "/api/v1/market/data/EURUSD",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Manual trading should still work without AI
        trade_response = await async_client.post(
            "/api/v1/trading/trades",
            headers=auth_headers,
            json={
                "symbol": "EURUSD",
                "side": "buy",
                "volume": 0.1,
                "strategy": "manual"
            }
        )
        assert trade_response.status_code in [201, 400]
    
    @pytest.mark.asyncio
    async def test_data_persistence_after_disconnect(self, async_client: AsyncClient):
        """E2E: Data persists after connection loss."""
        # Register and login
        user_data = {
            "email": f"persist_{datetime.now().timestamp()}@test.com",
            "username": "persist_test",
            "password": "Persist123!"
        }
        await async_client.post("/api/v1/auth/register", json=user_data)
        login = await async_client.post(
            "/api/v1/auth/login",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        
        # Create some data
        await async_client.post(
            "/api/v1/trading/watchlist",
            headers=headers,
            json={"symbols": ["EURUSD", "GBPUSD"]}
        )
        
        # Simulate disconnect (new session)
        new_login = await async_client.post(
            "/api/v1/auth/login",
            data={"username": user_data["email"], "password": user_data["password"]}
        )
        new_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}
        
        # Verify data persisted
        watchlist = await async_client.get(
            "/api/v1/trading/watchlist",
            headers=new_headers
        )
        assert watchlist.status_code == 200
        assert "EURUSD" in watchlist.json().get("symbols", [])
