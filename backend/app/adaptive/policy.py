from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class SelectionPolicy:
    """Prevents strategy thrashing and over-trading (rule-based)."""
    cooldown_seconds: int = 120
    hysteresis_delta: float = 12.0  # score difference required to switch

    last_strategy: Optional[str] = None
    last_selected_at: Optional[datetime] = None
    last_score: Optional[float] = None

    def allow(self, now: datetime, candidate_strategy: str, candidate_score: float) -> bool:
        if self.last_selected_at is None or self.last_strategy is None or self.last_score is None:
            return True

        # Cooldown: block switching
        if (now - self.last_selected_at) < timedelta(seconds=self.cooldown_seconds):
            return candidate_strategy == self.last_strategy

        # Hysteresis: require meaningful improvement to switch
        if candidate_strategy != self.last_strategy:
            return (candidate_score - self.last_score) >= self.hysteresis_delta

        return True

    def commit(self, now: datetime, strategy: str, score: float) -> None:
        self.last_strategy = strategy
        self.last_selected_at = now
        self.last_score = score 