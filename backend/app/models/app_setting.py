import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from app.database.connection import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(128), primary_key=True, index=True)
    value = Column(String, nullable=True)  # encrypted or plain (non-sensitive)
    is_secret = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)