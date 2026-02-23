from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base
import enum
import datetime
import uuid


class AlertType(str, enum.Enum):
    PRICE = "price"
    INDICATOR = "indicator"
    NEWS = "news"
    RISK = "risk"


class AlertCondition(str, enum.Enum):
    ABOVE = "above"
    BELOW = "below"
    CROSSING = "crossing"
    PERCENT_CHANGE = "percent_change"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    type = Column(Enum(AlertType), nullable=False)
    symbol = Column(String, nullable=False)
    condition = Column(Enum(AlertCondition), nullable=False)
    value = Column(Float, nullable=False)

    message_template = Column(Text, nullable=True)

    # ?????? Boolean ??? String
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # ? ?? ?????: ?? ?????? attribute ????? metadata (?????)
    # ?????? ??? ??? ?????? ?? DB ?? "metadata"
    metadata_json = Column("metadata", JSON, nullable=True)