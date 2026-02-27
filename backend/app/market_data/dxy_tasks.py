from __future__ import annotations

import logging

from app.services.notification_service import celery_app
from app.database.connection import get_db
from app.services.settings_service import SettingsService
from app.market_data.dxy_tracker import fetch_and_cache_dxy, due_for_refresh, mark_refreshed

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def refresh_dxy_context(self):
    """
    Beat calls this frequently; we decide internally if refresh is due,
    based on DB setting DXY_REFRESH_SECONDS.
    """
    try:
        import asyncio

        async def _run():
            async for db in get_db():
                svc = SettingsService(db)
                refresh_s = await svc.get("DXY_REFRESH_SECONDS")
                refresh_s = int(refresh_s) if refresh_s else 60

                if not due_for_refresh(refresh_s):
                    return {"skipped": True, "reason": "not_due"}

                # NOTE: we don't have real XAU price feed here; correlation is updated
                # mainly when analyze_market passes xau_last_close. Still refresh DXY.
                ctx = await fetch_and_cache_dxy(db, xau_last_close=None)
                mark_refreshed()
                return {"ok": True, "provider": ctx.provider, "dxy": ctx.current_dxy}

        return asyncio.run(_run())

    except Exception as e:
        logger.error(f"DXY refresh failed: {e}")
        raise self.retry(exc=e)