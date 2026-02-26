from app.mt5.connector import mt5_connector
from app.services.settings_service import SettingsService

@router.get("/mt5")
async def get_mt5_rates(
    symbol: str = "XAUUSD",
    timeframe: str = "M15",
    count: int = 300,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_trader),
):
    # Apply runtime MT5 endpoint override (from DB)
    svc = SettingsService(db)
    host = await svc.get("MT5_HOST")
    port = await svc.get("MT5_PORT")
    if host:
        mt5_connector.set_endpoint(host, int(port or 9000))

    resp = await mt5_connector.get_rates(symbol=symbol, timeframe=timeframe, count=count, timeout_ms=3500)
    if isinstance(resp, dict) and resp.get("error"):
        raise HTTPException(status_code=502, detail=f"MT5 bridge error: {resp.get('error')}")

    # Expect either {"rates":[...]} or list
    items = resp.get("rates") if isinstance(resp, dict) else resp
    if not isinstance(items, list):
        items = resp.get("items") if isinstance(resp, dict) else []
    if not isinstance(items, list):
        items = []

    # normalize keys to the frontend chart standard
    out = []
    for x in items:
        if not isinstance(x, dict):
            continue
        # common MT5 bridge keys: time/open/high/low/close/tick_volume or volume
        t = x.get("time") or x.get("timestamp")
        out.append(
            {
                "time": t,
                "open": x.get("open"),
                "high": x.get("high"),
                "low": x.get("low"),
                "close": x.get("close"),
                "volume": x.get("tick_volume") or x.get("volume"),
            }
        )

    return {"symbol": symbol, "timeframe": timeframe, "count": len(out), "candles": out, "source": "mt5"}