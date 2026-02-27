import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database.connection import Base

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    model_type = Column(String(32), nullable=False)  # lstm | xgboost | lightgbm | ensemble
    symbol = Column(String(32), nullable=False)
    timeframe = Column(String(16), nullable=False)

    version = Column(String(64), nullable=False)
    artifact_path = Column(String(512), nullable=False)

    metrics = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)