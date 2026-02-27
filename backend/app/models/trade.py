import uuid
import enum
import datetime

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base

class TradeStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    CANCELLED = "cancelled"

class TradeType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class Trade(Base):
    __tablename__ = "trades"

    # UUID column expects uuid.UUID objects when as_uuid=True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False)
    type = Column(Enum(TradeType), nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    volume = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    open_time = Column(DateTime, default=datetime.datetime.utcnow)
    close_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)