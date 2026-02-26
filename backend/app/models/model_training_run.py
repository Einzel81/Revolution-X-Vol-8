import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database.connection import Base

class ModelTrainingRun(Base):
    __tablename__ = "model_training_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    model_type = Column(String(32), nullable=False)
    symbol = Column(String(32), nullable=False)
    timeframe = Column(String(16), nullable=False)

    status = Column(String(32), nullable=False)  # started|success|failed
    metrics = Column(JSONB, nullable=True)
    error = Column(String(1024), nullable=True)

    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)