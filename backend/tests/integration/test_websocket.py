"""
Integration Tests for WebSocket Connections
Testing real-time data streams
"""
import pytest
import json
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


@pytest.mark.integration
class TestWebSocketMarketData:
    """Test WebSocket market data streams."""
    
    async def test_websocket_market_data_stream(self, async_client: AsyncClient):
        """Test market data streaming."""
        async with async_client.websocket_connect(
            "/ws/v1/market"
        ) as websocket:
            # Subscribe to symbol
            await websocket.send_json({
                "action": "subscribe",
                "symbols": ["EURUSD", "GBPUSD"]
            })
            
            # Receive confirmation
            response = await websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # Receive market data tick
            tick = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=5.0
            )
            
            assert tick["type"] == "tick"
            assert "symbol" in tick
            assert "bid" in tick
            assert "ask" in tick
            assert "timestamp" in tick
    
    async def test_websocket_ohlcv_stream(self, async_client: AsyncClient):
        """Test OHLCV candle streaming."""
        async with async_client.websocket_connect(
            "/ws/v1/market"
        ) as websocket:
            await websocket.send_json({
                "action": "subscribe_ohlcv",
                "symbol": "EURUSD",
                "timeframe": "M1"
            })
            
            candle = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=5.0
            )
            
            assert candle["type"] == "candle"
            assert "open" in candle
            assert "high" in candle
            assert "low" in candle
            assert "close" in candle
            assert "volume" in candle
    
    async def test_websocket_multiple_subscriptions(self, async_client: AsyncClient):
        """Test multiple symbol subscriptions."""
        async with async_client.websocket_connect(
            "/ws/v1/market"
        ) as websocket:
            # Subscribe to multiple symbols
            symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
            await websocket.send_json({
                "action": "subscribe",
                "symbols": symbols
            })
            
            received_symbols = set()
            for _ in range(10):  # Receive 10 ticks
                try:
                    tick = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=2.0
                    )
                    if tick["type"] == "tick":
                        received_symbols.add(tick["symbol"])
                except asyncio.TimeoutError:
                    break
            
            assert len(received_symbols) > 0


@pytest.mark.integration
class TestWebSocketTrading:
    """Test WebSocket trading operations."""
    
    async def test_websocket_trade_execution(self, async_client: AsyncClient, auth_headers):
        """Test trade execution via WebSocket."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        async with async_client.websocket_connect(
            f"/ws/v1/trading?token={token}"
        ) as websocket:
            # Place market order
            await websocket.send_json({
                "action": "place_order",
                "data": {
                    "symbol": "EURUSD",
                    "side": "buy",
                    "type": "market",
                    "volume": 0.1
                }
            })
            
            response = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=5.0
            )
            
            assert response["type"] in ["order_accepted", "order_rejected"]
            if response["type"] == "order_accepted":
                assert "order_id" in response
    
    async def test_websocket_position_updates(self, async_client: AsyncClient, auth_headers):
        """Test real-time position updates."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        async with async_client.websocket_connect(
            f"/ws/v1/trading?token={token}"
        ) as websocket:
            # Subscribe to position updates
            await websocket.send_json({
                "action": "subscribe_positions"
            })
            
            # Should receive current positions
            update = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=3.0
            )
            
            assert update["type"] == "positions_snapshot"
            assert "positions" in update
    
    async def test_websocket_order_updates(self, async_client: AsyncClient, auth_headers):
        """Test order status updates."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        async with async_client.websocket_connect(
            f"/ws/v1/trading?token={token}"
        ) as websocket:
            await websocket.send_json({
                "action": "subscribe_orders"
            })
            
            # Place pending order
            await websocket.send_json({
                "action": "place_order",
                "data": {
                    "symbol": "EURUSD",
                    "side": "buy",
                    "type": "limit",
                    "price": 1.0500,
                    "volume": 0.1
                }
            })
            
            # Should receive order status updates
            updates = []
            for _ in range(3):
                try:
                    update = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=2.0
                    )
                    updates.append(update)
                except asyncio.TimeoutError:
                    break
            
            assert len(updates) > 0


@pytest.mark.integration
class TestWebSocketAI:
    """Test WebSocket AI streams."""
    
    async def test_websocket_ai_predictions(self, async_client: AsyncClient, auth_headers):
        """Test AI prediction streaming."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        async with async_client.websocket_connect(
            f"/ws/v1/ai?token={token}"
        ) as websocket:
            await websocket.send_json({
                "action": "subscribe_predictions",
                "symbols": ["EURUSD"],
                "timeframe": "H1"
            })
            
            prediction = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=10.0
            )
            
            assert prediction["type"] == "prediction"
            assert "symbol" in prediction
            assert "direction" in prediction
            assert "confidence" in prediction
            assert "timestamp" in prediction
    
    async def test_websocket_ai_signals(self, async_client: AsyncClient, auth_headers):
        """Test AI trading signals."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        async with async_client.websocket_connect(
            f"/ws/v1/ai?token={token}"
        ) as websocket:
            await websocket.send_json({
                "action": "subscribe_signals",
                "strategy": "ensemble"
            })
            
            signal = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=15.0
            )
            
            assert signal["type"] == "trading_signal"
            assert "entry_price" in signal
            assert "stop_loss" in signal
            assert "take_profit" in signal


@pytest.mark.integration
class TestWebSocketNotifications:
    """Test WebSocket notifications."""
    
    async def test_price_alerts(self, async_client: AsyncClient, auth_headers):
        """Test price alert notifications."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        async with async_client.websocket_connect(
            f"/ws/v1/notifications?token={token}"
        ) as websocket:
            # Set price alert
            await websocket.send_json({
                "action": "set_alert",
                "alert": {
                    "symbol": "EURUSD",
                    "condition": "above",
                    "price": 1.1000
                }
            })
            
            # Receive confirmation
            response = await websocket.receive_json()
            assert response["type"] == "alert_set"
    
    async def test_risk_alerts(self, async_client: AsyncClient, auth_headers):
        """Test risk alert notifications."""
        token = auth_headers["Authorization"].replace("Bearer ", "")
        
        async with async_client.websocket_connect(
            f"/ws/v1/notifications?token={token}"
        ) as websocket:
            await websocket.send_json({
                "action": "subscribe_risk_alerts"
            })
            
            # Risk alerts are sent automatically when thresholds are breached
            # This tests the subscription mechanism


@pytest.mark.integration
class TestWebSocketPerformance:
    """Test WebSocket performance."""
    
    async def test_high_frequency_data(self, async_client: AsyncClient):
        """Test handling high-frequency data."""
        async with async_client.websocket_connect(
            "/ws/v1/market"
        ) as websocket:
            await websocket.send_json({
                "action": "subscribe",
                "symbols": ["EURUSD"]
            })
            
            messages_received = 0
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 5:
                try:
                    msg = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=1.0
                    )
                    messages_received += 1
                except asyncio.TimeoutError:
                    break
            
            # Should receive multiple ticks in 5 seconds
            assert messages_received > 10
    
    async def test_connection_stability(self, async_client: AsyncClient):
        """Test connection stability over time."""
        async with async_client.websocket_connect(
            "/ws/v1/market"
        ) as websocket:
            # Keep connection alive for 10 seconds
            for i in range(10):
                await websocket.send_json({
                    "action": "ping",
                    "id": i
                })
                
                response = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=2.0
                )
                
                assert response["type"] == "pong"
                assert response["id"] == i
                
                await asyncio.sleep(1)


@pytest.mark.integration
class TestWebSocketErrors:
    """Test WebSocket error handling."""
    
    async def test_invalid_json(self, async_client: AsyncClient):
        """Test handling invalid JSON."""
        async with async_client.websocket_connect(
            "/ws/v1/market"
        ) as websocket:
            await websocket.send_text("invalid json{")
            
            response = await websocket.receive_json()
            assert response["type"] == "error"
            assert "invalid json" in response["message"].lower()
    
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected WebSocket."""
        with pytest.raises(Exception):
            async with async_client.websocket_connect(
                "/ws/v1/trading"  # No token
            ) as websocket:
                await websocket.send_json({"action": "test"})
    
    async def test_invalid_action(self, async_client: AsyncClient):
        """Test invalid action handling."""
        async with async_client.websocket_connect(
            "/ws/v1/market"
        ) as websocket:
            await websocket.send_json({
                "action": "invalid_action"
            })
            
            response = await websocket.receive_json()
            assert response["type"] == "error"
            assert "unknown action" in response["message"].lower()
