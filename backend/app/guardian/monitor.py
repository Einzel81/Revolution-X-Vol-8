"""
Performance Monitor - مراقب الأداء
مراقبة مستمرة لمؤشرات الأداء الرئيسية (KPIs)
"""

import asyncio
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from collections import deque
import logging

from sqlalchemy.orm import Session
from .models import (
    PerformanceMetric, Alert, AlertSeverity, 
    PerformanceMetricDB, AlertDB
)

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    مراقب الأداء الذكي - يجمع المقاييس ويكتشف الانحرافات
    """
    
    # thresholds - الحدود الحرجة
    THRESHOLDS = {
        'win_rate': {'min': 0.55, 'target': 0.65},
        'profit_factor': {'min': 1.5, 'target': 2.0},
        'sharpe_ratio': {'min': 1.0, 'target': 1.5},
        'max_drawdown': {'max': -0.15, 'target': -0.10},
        'expectancy': {'min': 0.0, 'target': 0.02},
        'latency_ms': {'max': 100, 'target': 50}
    }
    
    def __init__(self, db_session: Session, check_interval: int = 300):
        """
        Args:
            db_session: جلسة قاعدة البيانات
            check_interval: الفاصل الزمني للفحص بالثواني (افتراضي 5 دقائق)
        """
        self.db = db_session
        self.check_interval = check_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # تخزين آخر 100 قياس للمتوسطات المتحركة
        self._metrics_history: Dict[str, deque] = {
            'win_rate': deque(maxlen=100),
            'profit_factor': deque(maxlen=100),
            'sharpe_ratio': deque(maxlen=100),
            'max_drawdown': deque(maxlen=100),
            'expectancy': deque(maxlen=100),
            'latency_ms': deque(maxlen=100)
        }
        
        # قائمة المستمعين للتنبيهات
        self._alert_handlers: List[Callable] = []
        
    def register_alert_handler(self, handler: Callable):
        """تسجيل دالة معالجة للتنبيهات"""
        self._alert_handlers.append(handler)
        
    async def start(self):
        """بدء المراقبة المستمرة"""
        if self.is_running:
            logger.warning("المonitor يعمل بالفعل")
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("✅ تم بدء مراقب الأداء")
        
    async def stop(self):
        """إيقاف المراقبة"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 تم إيقاف مراقب الأداء")
        
    async def _monitoring_loop(self):
        """الحلقة الرئيسية للمراقبة"""
        while self.is_running:
            try:
                await self.collect_metrics()
                await self.detect_anomalies()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"خطأ في حلقة المراقبة: {e}")
                await asyncio.sleep(60)  # انتظر دقيقة قبل إعادة المحاولة
                
    async def collect_metrics(self) -> PerformanceMetric:
        """
        جمع المقاييس من أنظمة التداول
        في الإنتاج، هذا يجب أن يقرأ من قاعدة بيانات التداول
        """
        # TODO: استبدل هذا بالاستعلام الفعلي من نظام التداول
        metrics = await self._fetch_trading_metrics()
        
        # حفظ في التاريخ
        for key, value in metrics.dict().items():
            if key in self._metrics_history and isinstance(value, (int, float)):
                self._metrics_history[key].append(value)
                
        # حفظ في قاعدة البيانات
        db_metric = PerformanceMetricDB(**metrics.dict())
        self.db.add(db_metric)
        self.db.commit()
        
        logger.debug(f"📊 تم جمع المقاييس: Win Rate={metrics.win_rate:.2%}")
        return metrics
        
    async def _fetch_trading_metrics(self) -> PerformanceMetric:
        """
        جلب المقاييس من نظام التداول الفعلي
        """
        # TODO: ربط هذا بنظام التداول الحقيقي
        # مثال مؤقت:
        return PerformanceMetric(
            win_rate=0.58,
            profit_factor=1.8,
            sharpe_ratio=1.2,
            max_drawdown=-0.12,
            expectancy=0.015,
            latency_ms=45,
            total_trades=150,
            successful_trades=87
        )
        
    async def detect_anomalies(self) -> List[Alert]:
        """
        اكتشاف الانحرافات عن المعدلات الطبيعية
        """
        alerts = []
        
        # جلب آخر مقياس
        latest = self.db.query(PerformanceMetricDB).order_by(
            PerformanceMetricDB.timestamp.desc()
        ).first()
        
        if not latest:
            return alerts
            
        # فحص كل مؤشر
        for metric_name, thresholds in self.THRESHOLDS.items():
            current_value = getattr(latest, metric_name, None)
            if current_value is None:
                continue
                
            # فحص الحدود المطلقة
            if 'min' in thresholds and current_value < thresholds['min']:
                deviation = (thresholds['min'] - current_value) / thresholds['min']
                alert = await self._create_alert(
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=thresholds['min'],
                    severity=self._calculate_severity(deviation),
                    message=f"انخفاض {metric_name}: {current_value:.3f} (الحد الأدنى: {thresholds['min']})"
                )
                alerts.append(alert)
                
            if 'max' in thresholds and current_value > thresholds['max']:
                deviation = (current_value - thresholds['max']) / abs(thresholds['max'])
                alert = await self._create_alert(
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=thresholds['max'],
                    severity=self._calculate_severity(deviation),
                    message=f"ارتفاع {metric_name}: {current_value:.3f} (الحد الأقصى: {thresholds['max']})"
                )
                alerts.append(alert)
                
            # فحص الانحراف عن المتوسط المتحرك (10%)
            if len(self._metrics_history[metric_name]) >= 20:
                moving_avg = statistics.mean(list(self._metrics_history[metric_name])[-20:])
                if moving_avg != 0:
                    deviation_pct = abs(current_value - moving_avg) / abs(moving_avg)
                    if deviation_pct > 0.10:
                        alert = await self._create_alert(
                            metric_name=f"{metric_name}_deviation",
                            current_value=current_value,
                            threshold_value=moving_avg,
                            severity=AlertSeverity.MEDIUM if deviation_pct < 0.20 else AlertSeverity.HIGH,
                            message=f"انحراف كبير في {metric_name}: {deviation_pct:.1%} عن المتوسط"
                        )
                        alerts.append(alert)
                        
        # إرسال التنبيهات للمستمعين
        for alert in alerts:
            await self._notify_handlers(alert)
            
        return alerts
        
    def _calculate_severity(self, deviation: float) -> AlertSeverity:
        """حساب مستوى الخطورة بناءً على نسبة الانحراف"""
        if deviation > 0.30:
            return AlertSeverity.CRITICAL
        elif deviation > 0.20:
            return AlertSeverity.HIGH
        elif deviation > 0.10:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW
        
    async def _create_alert(
        self, 
        metric_name: str, 
        current_value: float,
        threshold_value: float,
        severity: AlertSeverity,
        message: str
    ) -> Alert:
        """إنشاء تنبيه جديد"""
        # التحقق من عدم التكرار
        existing = self.db.query(AlertDB).filter(
            AlertDB.metric_name == metric_name,
            AlertDB.is_resolved == False
        ).first()
        
        if existing:
            # تحديث القيمة الحالية
            existing.current_value = current_value
            self.db.commit()
            return Alert.from_orm(existing)
            
        db_alert = AlertDB(
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message
        )
        self.db.add(db_alert)
        self.db.commit()
        self.db.refresh(db_alert)
        
        logger.warning(f"🚨 تنبيه جديد [{severity.value}]: {message}")
        return Alert.from_orm(db_alert)
        
    async def _notify_handlers(self, alert: Alert):
        """إشعار جميع المعالجين المسجلين"""
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"خطأ في معالج التنبيه: {e}")
                
    async def send_alert(self, alert: Alert):
        """إرسال تنبيه يدوي"""
        await self._notify_handlers(alert)
        
    def get_current_metrics(self) -> Optional[PerformanceMetric]:
        """الحصول على آخر مقاييس"""
        latest = self.db.query(PerformanceMetricDB).order_by(
            PerformanceMetricDB.timestamp.desc()
        ).first()
        return PerformanceMetric.from_orm(latest) if latest else None
        
    def get_active_alerts(self) -> List[Alert]:
        """الحصول على التنبيهات النشطة"""
        alerts = self.db.query(AlertDB).filter(
            AlertDB.is_resolved == False
        ).order_by(AlertDB.timestamp.desc()).all()
        return [Alert.from_orm(a) for a in alerts]
        
    def resolve_alert(self, alert_id: int):
        """حل تنبيه"""
        alert = self.db.query(AlertDB).filter(AlertDB.id == alert_id).first()
        if alert:
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"✅ تم حل التنبيه #{alert_id}")
