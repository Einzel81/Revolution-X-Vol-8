from __future__ import annotations

from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def log_router_decision(signal: Dict[str, Any]) -> None:
    """Lightweight telemetry (never breaks trading)."""
    try:
        adaptive = signal.get("adaptive") or {}
        regime = adaptive.get("regime") or {}
        selected = adaptive.get("selected") or {}
        logger.info(
            "adaptive_router_decision",
            extra={
                "action": signal.get("action"),
                "score": signal.get("score"),
                "confidence": signal.get("confidence"),
                "regime": regime,
                "selected": selected,
            },
        )
    except Exception:
        logger.debug("Failed to log router decision", exc_info=True) 