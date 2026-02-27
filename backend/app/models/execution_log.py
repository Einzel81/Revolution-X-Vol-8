# backend/app/models/execution_log.py

import datetime
import uuid

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.connection import Base


class ExecutionLog(Base):
    """
    Stores execution attempts / responses for MT5 or simulated mode.
    """
    __tablename__ = "execution_logs"

    # TimescaleDB hypertable requirement:
    # any PRIMARY KEY / UNIQUE index must include the time partition column.
    # We partition by created_at, so created_at is part of the composite PK.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id"), nullable=False)

    step = Column(String(64), nullable=False)  # send_order / response / retry / simulated / error
    attempt = Column(Integer, default=1, nullable=False)

    request = Column(JSONB, nullable=True)
    response = Column(JSONB, nullable=True)

    latency_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    error = Column(String(512), nullable=True)

    created_at = Column(DateTime, primary_key=True, default=datetime.datetime.utcnow, nullable=False)