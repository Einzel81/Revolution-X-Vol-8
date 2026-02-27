"""
API Endpoints for AI Code Guardian
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.auth.dependencies import get_current_user, require_admin
from app.guardian.monitor import PerformanceMonitor
from app.guardian.analyzer import CodeAnalyzer
from app.guardian.fixer import AutoFixer
from app.guardian.models import (
    PerformanceMetric, Alert, CodeChange, GuardianState,
    GuardianStatus, ChangeStatus
)
from app.guardian.knowledge_base import KnowledgeBase

router = APIRouter(prefix="/guardian", tags=["guardian"])

# Dependency to get monitor instance
def get_monitor(db: Session = Depends(get_db)):
    return PerformanceMonitor(db)

def get_analyzer(db: Session = Depends(get_db)):
    return CodeAnalyzer(db)

def get_fixer(db: Session = Depends(get_db)):
    return AutoFixer(db)

def get_knowledge(db: Session = Depends(get_db)):
    return KnowledgeBase(db)

# Response Models
class StatusResponse(BaseModel):
    status: str
    last_check: datetime
    active_models: List[str]
    pending_changes_count: int
    active_alerts_count: int
    uptime_hours: float

class MetricsResponse(BaseModel):
    current: PerformanceMetric
    history: List[PerformanceMetric]

class AlertResponse(BaseModel):
    alerts: List[Alert]
    total: int
    critical: int

class ChangeApprovalRequest(BaseModel):
    approved: bool
    comment: Optional[str] = None

# Endpoints

@router.get("/status", response_model=StatusResponse)
async def get_guardian_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على حالة Guardian"""
    monitor = PerformanceMonitor(db)
    fixer = AutoFixer(db)
    
    pending = len(fixer.get_pending_changes())
    alerts = len(monitor.get_active_alerts())
    
    return StatusResponse(
        status=GuardianStatus.OPERATIONAL.value,
        last_check=datetime.utcnow(),
        active_models=["gpt-4", "performance_monitor"],
        pending_changes_count=pending,
        active_alerts_count=alerts,
        uptime_hours=720.5  # TODO: حساب فعلي
    )

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على المقاييس"""
    from app.guardian.models import PerformanceMetricDB
    
    metrics = db.query(PerformanceMetricDB).order_by(
        PerformanceMetricDB.timestamp.desc()
    ).limit(limit).all()
    
    current = metrics[0] if metrics else None
    
    return MetricsResponse(
        current=PerformanceMetric.from_orm(current) if current else None,
        history=[PerformanceMetric.from_orm(m) for m in metrics]
    )

@router.get("/alerts", response_model=AlertResponse)
async def get_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على التنبيهات"""
    from app.guardian.models import AlertDB
    
    query = db.query(AlertDB)
    
    if severity:
        query = query.filter(AlertDB.severity == severity)
    if resolved is not None:
        query = query.filter(AlertDB.is_resolved == resolved)
        
    alerts = query.order_by(AlertDB.timestamp.desc()).all()
    
    critical = sum(1 for a in alerts if a.severity == "critical")
    
    return AlertResponse(
        alerts=[Alert.from_orm(a) for a in alerts],
        total=len(alerts),
        critical=critical
    )

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """حل تنبيه"""
    monitor = PerformanceMonitor(db)
    monitor.resolve_alert(alert_id)
    return {"message": "تم حل التنبيه"}

@router.get("/changes/pending", response_model=List[CodeChange])
async def get_pending_changes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على التغييرات المعلقة"""
    fixer = AutoFixer(db)
    return fixer.get_pending_changes()

@router.post("/changes/{change_id}/approve")
async def approve_change(
    change_id: int,
    request: ChangeApprovalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """الموافقة على تغيير"""
    fixer = AutoFixer(db)
    
    if request.approved:
        await fixer.approve_change(change_id, current_user.username)
        return {"message": "تمت الموافقة على التغيير", "change_id": change_id}
    else:
        await fixer.reject_change(change_id)
        return {"message": "تم رفض التغيير", "change_id": change_id}

@router.get("/history")
async def get_change_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """سجل التغييرات"""
    from app.guardian.models import CodeChangeDB
    
    changes = db.query(CodeChangeDB).order_by(
        CodeChangeDB.created_at.desc()
    ).limit(limit).all()
    
    return {
        "changes": [CodeChange.from_orm(c) for c in changes],
        "total": len(changes)
    }

@router.post("/trigger-analysis")
async def trigger_analysis(
    file_path: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """تشغيل تحليل يدوي"""
    analyzer = CodeAnalyzer(db)
    
    # تشغيل في الخلفية
    background_tasks.add_task(analyzer.analyze_strategy, file_path)
    
    return {
        "message": "تم بدء التحليل في الخلفية",
        "file": file_path
    }

@router.get("/knowledge/patterns")
async def get_knowledge_patterns(
    pattern_type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على أنماط قاعدة المعرفة"""
    kb = KnowledgeBase(db)
    
    query = db.query(KnowledgePatternDB)
    if pattern_type:
        query = query.filter(KnowledgePatternDB.pattern_type == pattern_type)
        
    patterns = query.order_by(
        KnowledgePatternDB.success_rate.desc()
    ).limit(limit).all()
    
    return {
        "patterns": [
            {
                "id": p.id,
                "type": p.pattern_type,
                "description": p.description,
                "success_rate": p.success_rate,
                "usage_count": p.usage_count
            }
            for p in patterns
        ]
    }

@router.get("/trends")
async def get_performance_trends(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """اتجاهات الأداء"""
    kb = KnowledgeBase(db)
    return kb.get_performance_trends()

@router.post("/start-monitoring")
async def start_monitoring(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """بدء المراقبة"""
    monitor = PerformanceMonitor(db)
    await monitor.start()
    return {"message": "تم بدء المراقبة"}

@router.post("/stop-monitoring")
async def stop_monitoring(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """إيقاف المراقبة"""
    monitor = PerformanceMonitor(db)
    await monitor.stop()
    return {"message": "تم إيقاف المراقبة"}
