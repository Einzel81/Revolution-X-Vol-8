"""
Notification Model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    TRADE_NEW = "trade_new"
    TRADE_CLOSED = "trade_closed"
    TRADE_PARTIAL_CLOSE = "trade_partial_close"
    RISK_DRAWDOWN = "risk_drawdown"
    RISK_CONSECUTIVE_LOSSES = "risk_consecutive_losses"
    RISK_MARGIN = "risk_margin"
    RISK_DAILY_LIMIT = "risk_daily_limit"
    PRICE_ALERT = "price_alert"
    GUARDIAN_OPTIMIZATION = "guardian_optimization"
    GUARDIAN_PARAMETER = "guardian_parameter"
    GUARDIAN_REPORT = "guardian_report"
    GUARDIAN_MODE = "guardian_mode"
    GUARDIAN_ANOMALY = "guardian_anomaly"
    SYSTEM_STATUS = "system_status"
    SYSTEM_MAINTENANCE = "system_maintenance"


class NotificationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification details
    type = Column(SQLEnum(NotificationType), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default=dict)  # Additional structured data
    
    # Delivery tracking
    channels = Column(JSON, default=list)  # ['telegram', 'email', 'push']
    delivered = Column(JSON, default=dict)  # {channel: timestamp}
    read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For temporary notifications
    
    # Relations
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id})>"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.utcnow()
    
    def mark_delivered(self, channel: str):
        """Mark as delivered on specific channel"""
        if not self.delivered:
            self.delivered = {}
        self.delivered[channel] = datetime.utcnow().isoformat()
