"""
نماذج البيانات لـ AI Code Guardian
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class ChangeType(str, Enum):
    HOTFIX = "hotfix"
    OPTIMIZATION = "optimization"
    PARAMETER_TUNING = "parameter_tuning"
    LOGIC_CHANGE = "logic_change"
    NEW_FEATURE = "new_feature"

class ChangeStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TESTING = "testing"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"

class GuardianStatus(str, Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    LEARNING = "learning"

# Database Models
class PerformanceMetricDB(Base):
    __tablename__ = "guardian_metrics"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    expectancy = Column(Float)
    latency_ms = Column(Float)
    total_trades = Column(Integer)
    successful_trades = Column(Integer)
    metric_metadata = Column("metadata", JSON)

class AlertDB(Base):
    __tablename__ = "guardian_alerts"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(SQLEnum(AlertSeverity))
    metric_name = Column(String(100))
    current_value = Column(Float)
    threshold_value = Column(Float)
    message = Column(Text)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    auto_fix_attempted = Column(Boolean, default=False)

class CodeChangeDB(Base):
    __tablename__ = "guardian_changes"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    change_type = Column(SQLEnum(ChangeType))
    status = Column(SQLEnum(ChangeStatus), default=ChangeStatus.PENDING)
    file_path = Column(String(500))
    original_code = Column(Text)
    proposed_code = Column(Text)
    description = Column(Text)
    reasoning = Column(Text)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    rollback_reason = Column(Text, nullable=True)
    test_results = Column(JSON, default=dict)
    performance_impact = Column(JSON, nullable=True)

class KnowledgePatternDB(Base):
    __tablename__ = "guardian_knowledge"
    
    id = Column(Integer, primary_key=True)
    pattern_type = Column(String(100))
    description = Column(Text)
    symptoms = Column(JSON)
    solution = Column(Text)
    success_rate = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

# Pydantic Models for API
class PerformanceMetric(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    win_rate: float = Field(..., ge=0, le=1)
    profit_factor: float = Field(..., ge=0)
    sharpe_ratio: float
    max_drawdown: float = Field(..., le=0)
    expectancy: float
    latency_ms: float = Field(..., ge=0)
    total_trades: int = Field(..., ge=0)
    successful_trades: int = Field(..., ge=0)
    
    class Config:
        from_attributes = True

class Alert(BaseModel):
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    is_resolved: bool = False
    
    class Config:
        from_attributes = True

class CodeChange(BaseModel):
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    change_type: ChangeType
    status: ChangeStatus = ChangeStatus.PENDING
    file_path: str
    original_code: str
    proposed_code: str
    description: str
    reasoning: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class GuardianState(BaseModel):
    status: GuardianStatus
    last_check: datetime
    active_models: List[str]
    pending_changes_count: int
    active_alerts_count: int
    uptime_hours: float
    
class AnalysisResult(BaseModel):
    issues_found: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    confidence_score: float
    analyzed_files: List[str]
