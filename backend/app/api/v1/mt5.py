from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_trader
from app.database.connection import get_db
from app.mt5.connector import mt5_connector
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/mt5", tags=["mt5"])

KEY_CONNECTIONS = "MT5_CONNECTIONS_JSON"
KEY_ACTIVE_ID = "MT5_CONNECTION_ACTIVE_ID"


class MT5ConnIn(BaseModel):
    name: str = Field(default="My MT5", min_length=1)
    host: str = Field(min_length=1)
    port: int = Field(default=9000, ge=1, le=65535)
    token: Optional[str] = None
    set_active: bool = True


def _now_ms() -> int:
    return int(time.time() * 1000)


def _safe_json_loads(s: Optional[str]) -> List[Dict[str, Any]]:
    if not s:
        return []
    try:
        v = json.loads(s)
        return v if isinstance(v, list) else []
    except Exception:
        return []


def _public_conn(c: Dict[str, Any], active_id: Optional[str]) -> Dict[str, Any]:
    return {
        "id": c.get("id"),
        "name": c.get("name"),
        "host": c.get("host"),
        "port": int(c.get("port") or 9000),
        "token": None,  # ?? ???? ??????
        "is_active": str(c.get("id")) == str(active_id),
        "created_at": c.get("created_at"),
        "updated_at": c.get("updated_at"),
    }


async def _settings_get(settings: SettingsService, key: str) -> Optional[str]:
    # ???? ?? decrypt ?? ???? 500 ??? ??? ?????? JSON ????
    try:
        return await settings.get(key, decrypt=False)
    except Exception:
        return None


async def _settings_set(settings: SettingsService, key: str, val: Any) -> None:
    try:
        # ???? JSON ??? plain
        await settings.set(key, val, is_secret=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"settings error: {e}")


def _set_endpoint_if_supported(host: str, port: int) -> None:
    fn = getattr(mt5_connector, "set_endpoint", None)
    if callable(fn):
        fn(host, port)


async def _ping_any() -> Dict[str, Any]:
    """
    ping ?? ???? sync ?? async - ?????? ???.
    """
    fn = getattr(mt5_connector, "ping", None)
    if not callable(fn):
        return {"ok": False, "error": "mt5_connector.ping not implemented"}

    res = fn()
    if hasattr(res, "__await__"):
        res = await res

    if isinstance(res, dict):
        return res
    return {"ok": True, "response": str(res)}


@router.get("/connections")
async def list_connections(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    settings = SettingsService(db)
    conns_raw = await _settings_get(settings, KEY_CONNECTIONS)
    conns = _safe_json_loads(conns_raw)
    active_id = await _settings_get(settings, KEY_ACTIVE_ID)

    items = [_public_conn(c, active_id) for c in conns]
    return {"count": len(items), "items": items, "active_id": active_id, "ts": _now_ms()}


@router.post("/connections")
async def create_connection(payload: MT5ConnIn, db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    settings = SettingsService(db)

    conns_raw = await _settings_get(settings, KEY_CONNECTIONS)
    conns = _safe_json_loads(conns_raw)

    cid = str(uuid.uuid4())
    row = {
        "id": cid,
        "name": payload.name.strip(),
        "host": payload.host.strip(),
        "port": int(payload.port),
        "token": payload.token.strip() if payload.token else None,
        "created_at": _now_ms(),
        "updated_at": _now_ms(),
    }
    conns.append(row)

    await _settings_set(settings, KEY_CONNECTIONS, json.dumps(conns, ensure_ascii=False))

    if payload.set_active:
        await _settings_set(settings, KEY_ACTIVE_ID, cid)
        _set_endpoint_if_supported(row["host"], row["port"])

    return {"ok": True, "id": cid, "ts": _now_ms()}


@router.post("/connections/{conn_id}/activate")
async def activate_connection(conn_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    settings = SettingsService(db)
    conns = _safe_json_loads(await _settings_get(settings, KEY_CONNECTIONS))

    found = next((c for c in conns if str(c.get("id")) == str(conn_id)), None)
    if not found:
        raise HTTPException(status_code=404, detail="connection not found")

    found["updated_at"] = _now_ms()
    await _settings_set(settings, KEY_CONNECTIONS, json.dumps(conns, ensure_ascii=False))
    await _settings_set(settings, KEY_ACTIVE_ID, str(conn_id))

    _set_endpoint_if_supported(found.get("host", "localhost"), int(found.get("port") or 9000))
    return {"ok": True, "active_id": str(conn_id), "ts": _now_ms()}


@router.get("/connections/active/ping")
async def ping_active(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    settings = SettingsService(db)
    conns = _safe_json_loads(await _settings_get(settings, KEY_CONNECTIONS))
    active_id = await _settings_get(settings, KEY_ACTIVE_ID)

    if not active_id:
        return {"ok": False, "detail": "no active connection", "ts": _now_ms()}

    active = next((c for c in conns if str(c.get("id")) == str(active_id)), None)
    if not active:
        return {"ok": False, "detail": "active connection not found", "ts": _now_ms()}

    _set_endpoint_if_supported(active.get("host", "localhost"), int(active.get("port") or 9000))

    resp = await _ping_any()
    resp["active_id"] = active_id
    resp["ts"] = _now_ms()
    return resp


def _unwrap_bridge_payload(resp: Any) -> Dict[str, Any]:
    """Normalize bridge payload to a dict.

    Some bridges return:
      - {"ok": True, "data": {...}}
      - {"response": {...}}
      - {...} directly
    """
    if not isinstance(resp, dict):
        return {"raw": resp}
    if "data" in resp and isinstance(resp.get("data"), dict):
        return resp["data"]
    if "response" in resp and isinstance(resp.get("response"), dict):
        return resp["response"]
    return resp


@router.get("/account")
async def get_account(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    """Return MT5 account info from the active ZMQ bridge."""
    settings = SettingsService(db)
    conns = _safe_json_loads(await _settings_get(settings, KEY_CONNECTIONS))
    active_id = await _settings_get(settings, KEY_ACTIVE_ID)
    if active_id:
        active = next((c for c in conns if str(c.get("id")) == str(active_id)), None)
        if active:
            _set_endpoint_if_supported(active.get("host", "localhost"), int(active.get("port") or 9000))

    fn = getattr(mt5_connector, "account_info", None)
    if not callable(fn):
        raise HTTPException(status_code=501, detail="mt5_connector.account_info not implemented")

    res = fn()
    if hasattr(res, "__await__"):
        res = await res

    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(status_code=503, detail={"ok": False, "error": res.get("error")})

    data = _unwrap_bridge_payload(res)
    out = {
        "balance": data.get("balance"),
        "equity": data.get("equity"),
        "margin": data.get("margin"),
        "free_margin": data.get("free_margin") or data.get("freeMargin"),
        "margin_level": data.get("margin_level") or data.get("marginLevel"),
        "currency": data.get("currency"),
        "login": data.get("login") or data.get("account") or data.get("account_id"),
    }
    return {"ok": True, "data": out, "raw": res, "active_id": active_id, "ts": _now_ms()}


@router.get("/positions")
async def get_positions(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    """Return MT5 open positions from the active ZMQ bridge."""
    settings = SettingsService(db)
    conns = _safe_json_loads(await _settings_get(settings, KEY_CONNECTIONS))
    active_id = await _settings_get(settings, KEY_ACTIVE_ID)
    if active_id:
        active = next((c for c in conns if str(c.get("id")) == str(active_id)), None)
        if active:
            _set_endpoint_if_supported(active.get("host", "localhost"), int(active.get("port") or 9000))

    fn = getattr(mt5_connector, "get_positions", None)
    if not callable(fn):
        raise HTTPException(status_code=501, detail="mt5_connector.get_positions not implemented")

    res = fn()
    if hasattr(res, "__await__"):
        res = await res

    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(status_code=503, detail={"ok": False, "error": res.get("error")})

    data = _unwrap_bridge_payload(res)
    items = data.get("positions") if isinstance(data.get("positions"), list) else None
    if items is None and isinstance(data.get("items"), list):
        items = data.get("items")
    if items is None and isinstance(res, list):
        items = res
    if items is None:
        items = data if isinstance(data, list) else []
    return {"ok": True, "count": len(items), "items": items, "raw": res, "active_id": active_id, "ts": _now_ms()}


@router.get("/orders")
async def get_orders(db: AsyncSession = Depends(get_db), user=Depends(require_trader)):
    """Return MT5 pending orders (if bridge supports it)."""
    settings = SettingsService(db)
    conns = _safe_json_loads(await _settings_get(settings, KEY_CONNECTIONS))
    active_id = await _settings_get(settings, KEY_ACTIVE_ID)
    if active_id:
        active = next((c for c in conns if str(c.get("id")) == str(active_id)), None)
        if active:
            _set_endpoint_if_supported(active.get("host", "localhost"), int(active.get("port") or 9000))

    fn = getattr(mt5_connector, "get_orders", None)
    if not callable(fn):
        return {"ok": False, "detail": "mt5_connector.get_orders not implemented", "active_id": active_id, "ts": _now_ms()}

    res = fn()
    if hasattr(res, "__await__"):
        res = await res

    if isinstance(res, dict) and res.get("error"):
        raise HTTPException(status_code=503, detail={"ok": False, "error": res.get("error")})

    data = _unwrap_bridge_payload(res)
    items = data.get("orders") if isinstance(data.get("orders"), list) else None
    if items is None and isinstance(data.get("items"), list):
        items = data.get("items")
    if items is None:
        items = data if isinstance(data, list) else []
    return {"ok": True, "count": len(items), "items": items, "raw": res, "active_id": active_id, "ts": _now_ms()}