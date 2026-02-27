import datetime
from sqlalchemy import Column, String, Float, DateTime, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import Base

class Candle(Base):
    __tablename__ = "candles"

    # Timescale best practice: time first
    time = Column(DateTime, primary_key=True, nullable=False)
    symbol = Column(String(32), primary_key=True, nullable=False)
    timeframe = Column(String(16), primary_key=True, nullable=False)

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)

    # Optional: ms epoch for fast ingestion dedup
    epoch_ms = Column(BigInteger, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

Index("ix_candles_symbol_tf_time", Candle.symbol, Candle.timeframe, Candle.time)