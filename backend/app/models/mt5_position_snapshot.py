from __future__ import annotations

import uuid
import datetime

from sqlalchemy import Column, String, Float, DateTime, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class MT5PositionSnapshot(Base):
    __tablename__ = "mt5_position_snapshots"
    __table_args__ = (UniqueConstraint("account_id", "ticket", name="uq_mt5_pos_account_ticket"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_id = Column(String, nullable=True)
    ticket = Column(String, nullable=False)

    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    volume = Column(Float, nullable=False)

    open_price = Column(Float, nullable=True)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)

    profit = Column(Float, nullable=True)
    swap = Column(Float, nullable=True)
    commission = Column(Float, nullable=True)

    open_time = Column(DateTime, nullable=True)
    magic = Column(String, nullable=True)
    comment = Column(String, nullable=True)

    raw = Column(JSON, nullable=True)