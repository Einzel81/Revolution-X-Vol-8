from __future__ import annotations

import uuid
import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.connection import Base


class PredictiveReport(Base):
    __tablename__ = "predictive_reports"

    # TimescaleDB hypertable requirement (partition by created_at):
    # PK/UNIQUE must include created_at.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    symbol = Column(String(32), nullable=False)
    timeframe = Column(String(16), nullable=False)

    wf_sharpe = Column(Float, nullable=True)
    wf_winrate = Column(Float, nullable=True)
    wf_avg_return = Column(Float, nullable=True)

    mc_max_dd = Column(Float, nullable=True)
    mc_var_95 = Column(Float, nullable=True)

    drift_score = Column(Float, nullable=True)
    stability_score = Column(Float, nullable=True)

    meta = Column(JSONB, nullable=True)
    created_at = Column(DateTime, primary_key=True, default=datetime.datetime.utcnow, nullable=False)