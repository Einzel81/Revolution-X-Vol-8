import pytest
from sqlalchemy import text

from app.core.config import settings
import app.core.trading_engine as te_mod


@pytest.mark.asyncio
async def test_live_execution_retries_persists_logs(async_client, db_session, monkeypatch):
    # Force live mode
    monkeypatch.setattr(settings, "EXECUTION_MODE", "live")
    monkeypatch.setattr(settings, "MT5_ORDER_RETRIES", 3)

    # Mock MT5: fail twice then succeed
    state = {"n": 0}

    async def fake_send_order(symbol, action, volume, sl, tp):
        state["n"] += 1
        if state["n"] < 3:
            return {"error": "temporary_failure"}
        return {"ticket": "123456", "ok": True}

    monkeypatch.setattr(te_mod.mt5_connector, "send_order", fake_send_order)

    resp = await async_client.post(
        "/api/v1/trading/execute",
        params={"symbol": "XAUUSD", "action": "BUY", "entry": 2000, "sl": 1990, "tp": 2020},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "executed"

    # 1 trade, 1 signal, 3 execution logs (2 fails + 1 success)
    r1 = await db_session.execute(text("SELECT COUNT(*) FROM trading_signals"))
    r2 = await db_session.execute(text("SELECT COUNT(*) FROM trades"))
    r3 = await db_session.execute(text("SELECT COUNT(*) FROM execution_logs"))

    assert int(r1.scalar() or 0) == 1
    assert int(r2.scalar() or 0) == 1
    assert int(r3.scalar() or 0) == 3