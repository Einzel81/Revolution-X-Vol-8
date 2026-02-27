# backend/app/strategies/kill_zones.py
"""
Kill Zones - Optimal Trading Sessions
- London Session (07:00 - 10:00 GMT)
- New York Session (13:00 - 16:00 GMT)
- Asian Session (00:00 - 08:00 GMT)
- London/NY Overlap (13:00 - 16:00 GMT) - Highest volatility
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, Literal
from enum import Enum
import pytz

class SessionType(Enum):
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    LONDON_NY_OVERLAP = "london_ny_overlap"
    OFF_HOURS = "off_hours"

@dataclass
class KillZone:
    session: SessionType
    is_active: bool
    start_time: time
    end_time: time
    volatility_rating: int  # 1-5
    liquidity_rating: int   # 1-5
    recommended: bool

class KillZoneAnalyzer:
    def __init__(self):
        # Define sessions in GMT
        self.sessions = {
            SessionType.ASIAN: {
                "start": time(0, 0),
                "end": time(8, 0),
                "volatility": 2,
                "liquidity": 2
            },
            SessionType.LONDON: {
                "start": time(7, 0),
                "end": time(16, 0),
                "volatility": 4,
                "liquidity": 4
            },
            SessionType.NEW_YORK: {
                "start": time(13, 0),
                "end": time(21, 0),
                "volatility": 4,
                "liquidity": 5
            },
            SessionType.LONDON_NY_OVERLAP: {
                "start": time(13, 0),
                "end": time(16, 0),
                "volatility": 5,
                "liquidity": 5
            }
        }
        
        self.gmt = pytz.timezone('GMT')
        
    def get_current_session(self, timestamp: Optional[datetime] = None) -> KillZone:
        """Determine current trading session"""
        if timestamp is None:
            timestamp = datetime.now(self.gmt)
        else:
            if timestamp.tzinfo is None:
                timestamp = pytz.utc.localize(timestamp).astimezone(self.gmt)
        
        current_time = timestamp.time()
        
        # Check for London/NY overlap first (highest priority)
        overlap = self.sessions[SessionType.LONDON_NY_OVERLAP]
        if overlap["start"] <= current_time < overlap["end"]:
            return KillZone(
                session=SessionType.LONDON_NY_OVERLAP,
                is_active=True,
                start_time=overlap["start"],
                end_time=overlap["end"],
                volatility_rating=overlap["volatility"],
                liquidity_rating=overlap["liquidity"],
                recommended=True
            )
        
        # Check other sessions
        for session_type, info in self.sessions.items():
            if session_type == SessionType.LONDON_NY_OVERLAP:
                continue
                
            if info["start"] <= current_time < info["end"]:
                # Check if this is London or NY session (but not overlap)
                is_recommended = session_type in [SessionType.LONDON, SessionType.NEW_YORK]
                
                return KillZone(
                    session=session_type,
                    is_active=True,
                    start_time=info["start"],
                    end_time=info["end"],
                    volatility_rating=info["volatility"],
                    liquidity_rating=info["liquidity"],
                    recommended=is_recommended
                )
        
        # Off hours
        return KillZone(
            session=SessionType.OFF_HOURS,
            is_active=False,
            start_time=time(21, 0),
            end_time=time(0, 0),
            volatility_rating=1,
            liquidity_rating=1,
            recommended=False
        )
    
    def should_trade(self, timestamp: Optional[datetime] = None) -> dict:
        """Determine if we should trade now"""
        zone = self.get_current_session(timestamp)
        
        # Trading rules
        can_trade = zone.recommended and zone.liquidity_rating >= 4
        
        reasons = []
        if not zone.is_active:
            reasons.append("Market is in off-hours")
        if zone.volatility_rating < 3:
            reasons.append("Low volatility period")
        if zone.liquidity_rating < 4:
            reasons.append("Insufficient liquidity")
        
        return {
            "can_trade": can_trade,
            "session": zone.session.value,
            "volatility": zone.volatility_rating,
            "liquidity": zone.liquidity_rating,
            "reasons": reasons if not can_trade else []
        }
    
    def get_next_session(self, timestamp: Optional[datetime] = None) -> dict:
        """Get info about next trading session"""
        if timestamp is None:
            timestamp = datetime.now(self.gmt)
        
        current_time = timestamp.time()
        
        # Find next session
        sessions_sorted = sorted(
            self.sessions.items(),
            key=lambda x: x[1]["start"]
        )
        
        for session_type, info in sessions_sorted:
            if info["start"] > current_time:
                # Found next session
                now = datetime.combine(timestamp.date(), current_time)
                start = datetime.combine(timestamp.date(), info["start"])
                
                # Handle midnight crossover
                if info["start"] < current_time:
                    start += timedelta(days=1)
                
                minutes_until = int((start - now).total_seconds() / 60)
                
                return {
                    "session": session_type.value,
                    "starts_in_minutes": minutes_until,
                    "start_time": info["start"].strftime("%H:%M"),
                    "volatility": info["volatility"],
                    "liquidity": info["liquidity"]
                }
        
        # Next session is tomorrow's Asian
        tomorrow = timestamp + timedelta(days=1)
        start = datetime.combine(tomorrow.date(), time(0, 0))
        now = datetime.combine(timestamp.date(), current_time)
        minutes_until = int((start - now).total_seconds() / 60)
        
        return {
            "session": "asian",
            "starts_in_minutes": minutes_until,
            "start_time": "00:00",
            "volatility": 2,
            "liquidity": 2
        }
    
    def get_session_highlights(self) -> list:
        """Get all sessions with their characteristics"""
        highlights = []
        
        for session_type, info in self.sessions.items():
            highlights.append({
                "session": session_type.value,
                "start": info["start"].strftime("%H:%M"),
                "end": info["end"].strftime("%H:%M"),
                "volatility": "⭐" * info["volatility"],
                "liquidity": "💧" * info["liquidity"],
                "best_for": self._get_session_best_for(session_type)
            })
        
        return highlights
    
    def _get_session_best_for(self, session: SessionType) -> str:
        """Get what each session is best for"""
        best_for = {
            SessionType.ASIAN: "Range trading, preparing for London",
            SessionType.LONDON: "Trend continuation, breakout trading",
            SessionType.NEW_YORK: "High volatility, momentum trading",
            SessionType.LONDON_NY_OVERLAP: "Best liquidity, major moves"
        }
        return best_for.get(session, "Unknown")

from datetime import timedelta
