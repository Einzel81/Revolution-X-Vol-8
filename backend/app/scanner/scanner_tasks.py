from __future__ import annotations

import asyncio
import logging

from app.services.notification_service import celery_app
from app.database.connection import get_db
from app.services.settings_service import SettingsService
from app.scanner.execution_service import ScannerExecutionService

logger = logging.getLogger(__name__)


async def _run_auto_select_once() -> dict:
    async for db in get_db():
        settings = SettingsService(db)

        enabled = (str(await settings.get("AUTO_SELECT_ENABLED") or "false").lower() == "true")
        if not enabled:
            return {"ok": True, "skipped": True, "reason": "AUTO_SELECT_ENABLED=false"}

        # --- Predictive Gate (hard gate) ---
        try:
            from app.predictive.service import PredictiveService  # type: ignore

            pred = PredictiveService()
            max_age = int(await settings.get("PREDICTIVE_MAX_REPORT_AGE_MIN") or 360)
            min_stab = float(await settings.get("PREDICTIVE_STABILITY_MIN") or 120)

            ok, rep, reason = await pred.latest_report_ok(db, symbol="XAUUSD", timeframe="M15", max_age_minutes=max_age)
            if not ok:
                await settings.set("AUTO_SELECT_ENABLED", "false", is_secret=False)
                await settings.set("AUTO_SELECT_DISABLE_REASON", f"Auto-select blocked: {reason}", is_secret=False)
                return {"ok": True, "blocked": True, "reason": reason}

            stab = float(getattr(rep, "stability_score", 0.0) or 0.0)
            if stab < min_stab:
                await settings.set("AUTO_SELECT_ENABLED", "false", is_secret=False)
                await settings.set(
                    "AUTO_SELECT_DISABLE_REASON",
                    f"Auto-select blocked: stability={stab:.2f} < min={min_stab:.2f}",
                    is_secret=False,
                )
                return {"ok": True, "blocked": True, "reason": "stability_below_threshold", "stability": stab, "min": min_stab}
        except Exception as e:
            # ??? predictive ??? ???? ?? ???? ???????? ??? ?? ???? ????? ?????? ????? Fail.
            logger.warning("Predictive gate skipped due to error: %s", e)

        # --- Execute best scanner signal ---
        # system user id for automation (configurable)
        system_user_id = str(await settings.get("AUTO_SELECT_SYSTEM_USER_ID") or "system")

        # TODO: Replace with real balance fetching if available
        balance = float(await settings.get("AUTO_SELECT_SYSTEM_BALANCE") or 12450.0)

        out = await ScannerExecutionService.execute_best(
            db=db,
            user_id=system_user_id,
            balance=balance,
            symbol=None,          # optional pin: "XAUUSD"
            timeframe=None,       # optional pin: "M15"
            min_score=None,       # from settings
            min_confidence=None,  # from settings
            enforce_limits=True,
        )
        return out

    return {"ok": False, "error": "db_not_available"}


@celery_app.task(bind=True, name="scanner.auto_select")
def scanner_auto_select(self) -> dict:
    try:
        return asyncio.run(_run_auto_select_once())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_run_auto_select_once())
        finally:
            try:
                loop.close()
            except Exception:
                pass
    except Exception as e:
        logger.exception("scanner_auto_select failed: %s", e)
        return {"ok": False, "error": str(e)}