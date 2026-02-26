import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_execute_trade_persists_signal_trade_and_execution(async_client, db_session):
    resp = await async_client.post(
        "/api/v1/trading/execute",
        params={
            "symbol": "XAUUSD",
            "action": "BUY",
            "entry": 2000.0,
            "sl": 1990.0,
            "tp": 2020.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("simulated", "executed")

    # Verify inserts
    r1 = await db_session.execute(text("SELECT COUNT(*) FROM trading_signals"))
    r2 = await db_session.execute(text("SELECT COUNT(*) FROM trades"))
    r3 = await db_session.execute(text("SELECT COUNT(*) FROM execution_logs"))

    assert int(r1.scalar() or 0) == 1
    assert int(r2.scalar() or 0) == 1
    assert int(r3.scalar() or 0) == 1