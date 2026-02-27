from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json
import time

import redis

from app.core.config import settings
from app.services.settings_service import SettingsService
from app.market_data.providers.yahoo import YahooDXYProvider
from app.market_data.providers.twelvedata import TwelveDataDXYProvider
from app.market_data.providers.fmp import FMPDXYProvider
from app.market_data.correlation import rolling_corr, corr_strength

REDIS_CTX_KEY = "market:dxy:context"
REDIS_LAST_RUN_KEY = "market:dxy:last_refresh_ts"

# rolling series for corr
REDIS_SERIES_XAU = "market:series:xau"
REDIS_SERIES_DXY = "market:series:dxy"
SERIES_MAXLEN = 120  # enough for rolling corr


@dataclass(frozen=True)
class DXYContext:
    provider: str
    symbol: str
    current_dxy: float
    impact: str       # bullish | bearish | neutral (impact on GOLD)
    strength: str     # low | moderate | strong
    corr_rolling: Optional[float]
    corr_strength: str
    updated_at: int


def _redis() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _compute_impact_strength(prev: Optional[float], curr: float) -> tuple[str, str]:
    if prev is None:
        return "neutral", "low"

    delta = curr - prev
    ad = abs(delta)

    if ad < 0.03:
        return "neutral", "low"

    impact = "bearish" if delta > 0 else "bullish"  # DXY up => Gold bearish
    if ad >= 0.12:
        strength = "strong"
    elif ad >= 0.06:
        strength = "moderate"
    else:
        strength = "low"

    return impact, strength


def _parse_series(r: redis.Redis, key: str) -> List[float]:
    vals = r.lrange(key, 0, -1)
    out: List[float] = []
    for v in vals:
        try:
            out.append(float(v))
        except Exception:
            continue
    return out


async def _load_cfg(db) -> Dict[str, Any]:
    svc = SettingsService(db)

    provider = (await svc.get("DXY_PROVIDER")) or settings.DXY_PROVIDER
    refresh = (await svc.get("DXY_REFRESH_SECONDS")) or str(settings.DXY_REFRESH_SECONDS)
    ttl = (await svc.get("DXY_CACHE_TTL_SECONDS")) or str(settings.DXY_CACHE_TTL_SECONDS)

    api_key = await svc.get("DXY_API_KEY", decrypt=True)
    if not api_key:
        api_key = settings.DXY_API_KEY

    # execution mode can be read similarly later if you want
    return {
        "provider": str(provider),
        "refresh_seconds": int(refresh),
        "ttl_seconds": int(ttl),
        "api_key": api_key,
    }


def _build_provider_chain(primary: str, api_key: Optional[str]):
    chain = []
    # prefer the selected one first
    order = [primary, "twelvedata", "fmp", "yahoo"]
    seen = set()
    for p in order:
        if p in seen:
            continue
        seen.add(p)
        if p == "twelvedata":
            if api_key:
                chain.append(TwelveDataDXYProvider(api_key=api_key, symbol="DXY"))
        elif p == "fmp":
            if api_key:
                chain.append(FMPDXYProvider(api_key=api_key, symbol="DXY"))
        else:
            chain.append(YahooDXYProvider(symbol="DX-Y.NYB"))
    return chain


async def fetch_and_cache_dxy(db, *, xau_last_close: Optional[float] = None) -> DXYContext:
    cfg = await _load_cfg(db)
    primary = cfg["provider"]
    api_key = cfg.get("api_key")

    r = _redis()

    prev_ctx_raw = r.get(REDIS_CTX_KEY)
    prev_price = None
    if prev_ctx_raw:
        try:
            prev_price = float(json.loads(prev_ctx_raw).get("current_dxy"))
        except Exception:
            prev_price = None

    provider_chain = _build_provider_chain(primary, api_key)

    last_error = None
    quote = None
    used_provider = primary
    for p in provider_chain:
        try:
            q = await p.get_quote()
            quote = q
            used_provider = getattr(p, "name", primary)
            break
        except Exception as e:
            last_error = str(e)

    if quote is None:
        raise RuntimeError(f"DXY providers failed. last_error={last_error}")

    impact, strength = _compute_impact_strength(prev_price, quote.price)

    # Update rolling series for corr
    if xau_last_close is not None:
        r.rpush(REDIS_SERIES_XAU, float(xau_last_close))
        r.ltrim(REDIS_SERIES_XAU, -SERIES_MAXLEN, -1)
    r.rpush(REDIS_SERIES_DXY, float(quote.price))
    r.ltrim(REDIS_SERIES_DXY, -SERIES_MAXLEN, -1)

    xau_series = _parse_series(r, REDIS_SERIES_XAU)
    dxy_series = _parse_series(r, REDIS_SERIES_DXY)

    c = rolling_corr(xau_series, dxy_series)
    c, c_strength = corr_strength(c)

    ctx = DXYContext(
        provider=used_provider,
        symbol=quote.symbol,
        current_dxy=float(quote.price),
        impact=impact,
        strength=strength,
        corr_rolling=c,
        corr_strength=c_strength,
        updated_at=int(time.time()),
    )

    payload = json.dumps({
        "provider": ctx.provider,
        "symbol": ctx.symbol,
        "current_dxy": ctx.current_dxy,
        "impact": ctx.impact,
        "strength": ctx.strength,
        "corr_rolling": ctx.corr_rolling,
        "corr_strength": ctx.corr_strength,
        "updated_at": ctx.updated_at,
    })

    r.setex(REDIS_CTX_KEY, int(cfg["ttl_seconds"]), payload)
    return ctx


def get_cached_dxy_context() -> Optional[Dict[str, Any]]:
    r = _redis()
    raw = r.get(REDIS_CTX_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def due_for_refresh(refresh_seconds: int) -> bool:
    r = _redis()
    last = r.get(REDIS_LAST_RUN_KEY)
    now = int(time.time())
    if not last:
        return True
    try:
        last_i = int(float(last))
    except Exception:
        return True
    return (now - last_i) >= int(refresh_seconds)


def mark_refreshed():
    r = _redis()
    r.set(REDIS_LAST_RUN_KEY, str(int(time.time())))


def push_xau_price(xau_last_close: float) -> None:
    """
    Push XAU close into rolling series in Redis (no DB required).
    """
    r = _redis()
    r.rpush(REDIS_SERIES_XAU, float(xau_last_close))
    r.ltrim(REDIS_SERIES_XAU, -SERIES_MAXLEN, -1)


def recompute_corr_and_update_context() -> Optional[Dict[str, Any]]:
    """
    Recompute rolling correlation using current series (XAU & DXY) and update cached context in Redis.
    Does NOT fetch new DXY price.
    """
    r = _redis()

    ctx_raw = r.get(REDIS_CTX_KEY)
    if not ctx_raw:
        return None

    try:
        ctx = json.loads(ctx_raw)
        if not isinstance(ctx, dict):
            return None
    except Exception:
        return None

    xau_series = _parse_series(r, REDIS_SERIES_XAU)
    dxy_series = _parse_series(r, REDIS_SERIES_DXY)

    c = rolling_corr(xau_series, dxy_series)
    c, c_strength = corr_strength(c)

    ctx["corr_rolling"] = c
    ctx["corr_strength"] = c_strength

    # Preserve remaining TTL if possible
    ttl = r.ttl(REDIS_CTX_KEY)
    payload = json.dumps(ctx)

    if ttl and ttl > 0:
        r.setex(REDIS_CTX_KEY, ttl, payload)
    else:
        # fallback: keep default ttl
        r.setex(REDIS_CTX_KEY, int(settings.DXY_CACHE_TTL_SECONDS), payload)

    return ctx