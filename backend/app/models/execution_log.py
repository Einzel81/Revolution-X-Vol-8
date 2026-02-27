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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id"), nullable=False)

    step = Column(String(64), nullable=False)  # send_order / response / retry / simulated / error
    attempt = Column(Integer, default=1, nullable=False)

    request = Column(JSONB, nullable=True)
    response = Column(JSONB, nullable=True)

    latency_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    error = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)