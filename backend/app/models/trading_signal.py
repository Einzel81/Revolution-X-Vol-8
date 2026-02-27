# backend/app/models/trading_signal.py

import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.connection import Base


class TradingSignal(Base):
    """
    Stores a generated signal snapshot (engine/router output + context).
    """
    __tablename__ = "trading_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    source = Column(String(32), nullable=False, default="engine")  # engine | scanner | webhook
    symbol = Column(String(32), nullable=False)
    timeframe = Column(String(16), nullable=True)

    action = Column(String(32), nullable=False)  # BUY/SELL/NEUTRAL/WAIT/STRONG_*
    confidence = Column(Float, nullable=True)
    score = Column(Float, nullable=True)

    entry_price = Column(Float, nullable=True)
    suggested_sl = Column(Float, nullable=True)
    suggested_tp = Column(Float, nullable=True)

    reasons = Column(JSONB, nullable=True)
    context = Column(JSONB, nullable=True)  # regime/scores/dxy/filters/etc.

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)