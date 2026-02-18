"""
Knowledge Base - قاعدة المعرفة
تخزين الأنماط والحلول للاستخدام المستقبلي
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import KnowledgePatternDB

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """
    قاعدة معرفة Guardian - تتعلم من التجارب
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    async def store_pattern(
        self,
        pattern_type: str,
        description: str,
        symptoms: List[str],
        solution: str,
        context: Optional[Dict] = None
    ) -> int:
        """
        تخزين نمط جديد في القاعدة
        """
        pattern = KnowledgePatternDB(
            pattern_type=pattern_type,
            description=description,
            symptoms=json.dumps(symptoms),
            solution=solution,
            success_rate=0.0,
            usage_count=0
        )
        
        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)
        
        logger.info(f"📚 تم تخزين نمط جديد #{pattern.id}: {pattern_type}")
        return pattern.id
        
    async def retrieve_similar(
        self,
        symptoms: List[str],
        pattern_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        استرجاع أنماط مشابهة بناءً على الأعراض
        """
        query = self.db.query(KnowledgePatternDB)
        
        if pattern_type:
            query = query.filter(KnowledgePatternDB.pattern_type == pattern_type)
            
        # البحث عن تطابق جزئي في الأعراض
        patterns = query.order_by(
            KnowledgePatternDB.success_rate.desc()
        ).limit(limit * 2).all()
        
        # حساب التشابه
        scored_patterns = []
        for pattern in patterns:
            pattern_symptoms = json.loads(pattern.symptoms)
            similarity = self._calculate_similarity(symptoms, pattern_symptoms)
            scored_patterns.append((similarity, pattern))
            
        # ترتيب حسب التشابه ثم نسبة النجاح
        scored_patterns.sort(key=lambda x: (x[0], x[1].success_rate), reverse=True)
        
        results = []
        for similarity, pattern in scored_patterns[:limit]:
            if similarity > 0.3:  # حد أدنى للتشابه
                results.append({
                    "id": pattern.id,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "symptoms": json.loads(pattern.symptoms),
                    "solution": pattern.solution,
                    "success_rate": pattern.success_rate,
                    "similarity_score": similarity,
                    "usage_count": pattern.usage_count
                })
                
        return results
        
    def _calculate_similarity(self, symptoms1: List[str], symptoms2: List[str]) -> float:
        """حساب تشابه قائمتين من الأعراض"""
        if not symptoms1 or not symptoms2:
            return 0.0
            
        set1 = set(s.lower() for s in symptoms1)
        set2 = set(s.lower() for s in symptoms2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
        
    async def learn_from_history(self, days: int = 30):
        """
        التعلم من التاريخ - تحليل الأنماط الناجحة والفاشلة
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # تحليل التغييرات الناجحة
        successful = self.db.query(CodeChangeDB).filter(
            CodeChangeDB.status == ChangeStatus.DEPLOYED,
            CodeChangeDB.deployed_at >= since
        ).all()
        
        # تحديث نسب النجاح
        for change in successful:
            # البحث عن أنماط مشابهة
            patterns = self.db.query(KnowledgePatternDB).filter(
                KnowledgePatternDB.pattern_type == change.change_type.value
            ).all()
            
            for pattern in patterns:
                pattern.success_rate = (
                    (pattern.success_rate * pattern.usage_count + 1) / 
                    (pattern.usage_count + 1)
                )
                pattern.usage_count += 1
                
        self.db.commit()
        logger.info(f"📈 تم تحديث قاعدة المعرفة بناءً على {len(successful)} تغيير ناجح")
        
    async def get_strategy_evolution_suggestions(self) -> List[Dict[str, Any]]:
        """
        اقتراحات تطور الاستراتيجية بناءً على تغيرات السوق
        """
        # تحليل آخر 7 أيام
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # البحث عن أنماط الأداء المتغيرة
        recent_patterns = self.db.query(KnowledgePatternDB).filter(
            KnowledgePatternDB.pattern_type == "market_change",
            KnowledgePatternDB.created_at >= week_ago
        ).all()
        
        suggestions = []
        for pattern in recent_patterns:
            suggestions.append({
                "type": "strategy_evolution",
                "description": pattern.description,
                "recommended_action": pattern.solution,
                "confidence": pattern.success_rate,
                "based_on_pattern": pattern.id
            })
            
        return suggestions
        
    async def record_bug_pattern(
        self,
        error_type: str,
        stack_trace: str,
        root_cause: str,
        fix_applied: str
    ):
        """
        تسجيل نمط خطأ للتعلم منه
        """
        symptoms = [
            error_type,
            stack_trace.split("\n")[0] if stack_trace else "",
            root_cause[:100]
        ]
        
        await self.store_pattern(
            pattern_type="bug",
            description=f"خطأ: {error_type}",
            symptoms=symptoms,
            solution=fix_applied,
            context={"stack_trace": stack_trace}
        )
        
    def get_performance_trends(self) -> Dict[str, Any]:
        """
        تحليل اتجاهات الأداء
        """
        # جلب آخر 30 يوم
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        metrics = self.db.query(PerformanceMetricDB).filter(
            PerformanceMetricDB.timestamp >= month_ago
        ).order_by(PerformanceMetricDB.timestamp).all()
        
        if len(metrics) < 7:
            return {"trend": "insufficient_data"}
            
        # حساب الاتجاه
        win_rates = [m.win_rate for m in metrics]
        trend = "improving" if win_rates[-1] > win_rates[0] else "declining"
        
        # التنبيه المبكر
        early_warning = False
        if len(win_rates) >= 5:
            last_5_avg = sum(win_rates[-5:]) / 5
            prev_5_avg = sum(win_rates[-10:-5]) / 5 if len(win_rates) >= 10 else last_5_avg
            
            if last_5_avg < prev_5_avg * 0.95:  # انخفاض 5%
                early_warning = True
                
        return {
            "trend": trend,
            "current_win_rate": win_rates[-1],
            "win_rate_change": win_rates[-1] - win_rates[0],
            "early_warning": early_warning,
            "recommendation": "review_strategy" if early_warning else "continue"
        }
