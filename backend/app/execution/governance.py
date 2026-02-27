from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_event import ExecutionEvent
from app.services.settings_service import SettingsService


@dataclass
class ExecGovernanceDecision:
    allow: bool
    reason: Optional[str] = None
    disable_auto_select: bool = False


class ExecutionGovernance:
    """Execution governance gates.

    - Block automation when unsafe.
    - For manual trades: avoid hard-block, record telemetry.

    Settings keys:
    - AUTO_SELECT_ENABLED
    - EXEC_GUARD_ENABLED
    - EXEC_DISABLE_AUTO_ON_VIOLATION
    - EXEC_VIOLATION_WINDOW_MIN
    - EXEC_MAX_VIOLATIONS_IN_WINDOW
    """

    async def pre_trade_gate(
        self,
        db: AsyncSession,
        *,
        source: str,
        bridge_connected: bool,
        is_automation: bool,
    ) -> ExecGovernanceDecision:
        settings = SettingsService(db)

        guard_enabled = (str(await settings.get("EXEC_GUARD_ENABLED") or "true").lower() == "true")
        if not guard_enabled:
            return ExecGovernanceDecision(allow=True)

        if is_automation:
            auto_enabled = (str(await settings.get("AUTO_SELECT_ENABLED") or "false").lower() == "true")
            if not auto_enabled:
                return ExecGovernanceDecision(allow=False, reason="AUTO_SELECT_ENABLED=false")

        if not bridge_connected and is_automation:
            return ExecGovernanceDecision(allow=False, reason="bridge_disconnected")

        return ExecGovernanceDecision(allow=True)

    async def post_trade_update(
        self,
        db: AsyncSession,
        *,
        violated: bool,
        violation_reason: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        if not violated:
            return False, None

        settings = SettingsService(db)
        disable_auto = (str(await settings.get("EXEC_DISABLE_AUTO_ON_VIOLATION") or "true").lower() == "true")
        if not disable_auto:
            return False, None

        window_min = int(await settings.get("EXEC_VIOLATION_WINDOW_MIN") or 15)
        max_viol = int(await settings.get("EXEC_MAX_VIOLATIONS_IN_WINDOW") or 3)
        since = datetime.utcnow() - timedelta(minutes=window_min)

        q = (
            select(ExecutionEvent)
            .where((ExecutionEvent.created_at >= since) & (ExecutionEvent.status == "bad"))
            .order_by(desc(ExecutionEvent.created_at))
            .limit(max_viol)
        )
        rows = (await db.execute(q)).scalars().all()
        if len(rows) < max_viol:
            return False, None

        await settings.set("AUTO_SELECT_ENABLED", "false", is_secret=False)
        reason = violation_reason or "execution_violation"
        await settings.set(
            "AUTO_SELECT_DISABLE_REASON",
            f"Execution guard: {reason} (bad>={max_viol} in {window_min}m)",
            is_secret=False,
        )
        return True, reason


execution_governance = ExecutionGovernance()