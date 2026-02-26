from __future__ import annotations

import uuid
import datetime

from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class ExecutionEvent(Base):
    """Execution telemetry for every order attempt (live or blocked)."""

    __tablename__ = "execution_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # who triggered
    user_id = Column(String, nullable=True)
    source = Column(String, nullable=False, default="system")  # api | celery | system

    # trade info
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # BUY | SELL
    volume = Column(Float, nullable=False)
    requested_price = Column(Float, nullable=True)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)

    # execution result
    status = Column(String, nullable=False)  # success | rejected | blocked | error | simulated
    ticket = Column(String, nullable=True)
    fill_price = Column(Float, nullable=True)
    slippage = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    bridge_connected = Column(Boolean, default=False)

    error = Column(String, nullable=True)
    request = Column(JSON, nullable=True)
    response = Column(JSON, nullable=True)