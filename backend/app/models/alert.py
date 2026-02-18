"""
Alert Model - User-defined alerts
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.app.core.database import Base


class AlertType(str, enum.Enum):
    PRICE = "price"
    RISK = "risk"
    MARGIN_CALL = "margin_call"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    EMERGENCY = "emergency"


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Alert configuration
    type = Column(SQLEnum(AlertType), nullable=False)
    trigger = Column(String(50), nullable=False)  # e.g., 'price_above', 'drawdown_percent'
    symbol = Column(String(20), nullable=True)  # For price alerts
    
    condition_value = Column(Float, nullable=False)  # Threshold value
    condition_operator = Column(String(10), default=">=")  # >=, <=, ==, etc.
    
    # Message template
    message_template = Column(Text, nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=60)  # Minimum time between triggers
    max_triggers = Column(Integer, nullable=True)  # Max times to trigger (null = unlimited)
    trigger_count = Column(Integer, default=0)
    
    # Notification channels
    notification_channels = Column(JSON, default=lambda: ["telegram"])
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.type}, trigger={self.trigger})>"
    
    def can_trigger(self) -> bool:
        """Check if alert can be triggered (cooldown check)"""
        if not self.is_active:
            return False
        
        if self.max_triggers and self.trigger_count >= self.max_triggers:
            return False
        
        if self.last_triggered and self.cooldown_minutes:
            from datetime import timedelta
            cooldown_end = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False
        
        return True
    
    def record_trigger(self):
        """Record that alert was triggered"""
        self.last_triggered = datetime.utcnow()
        self.trigger_count += 1
