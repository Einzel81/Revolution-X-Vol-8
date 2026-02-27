"""
Auto-Fixer - المصلح الذكي
تصنيف المشاكل وتطبيق الإصلاحات تلقائياً
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session
from .llm_interface import LLMInterface
from .models import CodeChange, ChangeType, ChangeStatus, CodeChangeDB
from .tester import SafeTester

logger = logging.getLogger(__name__)

class ApprovalLevel(str, Enum):
    AUTO = "auto"           # تلقائي
    SEMI_AUTO = "semi_auto" # نصف تلقائي (يتطلب موافقة)
    MANUAL = "manual"       # يدوي

class AutoFixer:
    """
    المصلح الذكي - يصلح المشاكل حسب نوعها
    """
    
    # تعيين مستوى الموافقة لكل نوع
    APPROVAL_MAP = {
        ChangeType.HOTFIX: ApprovalLevel.AUTO,
        ChangeType.OPTIMIZATION: ApprovalLevel.AUTO,
        ChangeType.PARAMETER_TUNING: ApprovalLevel.SEMI_AUTO,
        ChangeType.LOGIC_CHANGE: ApprovalLevel.MANUAL,
        ChangeType.NEW_FEATURE: ApprovalLevel.MANUAL
    }
    
    def __init__(
        self, 
        db_session: Session, 
        llm_interface: Optional[LLMInterface] = None,
        tester: Optional[SafeTester] = None
    ):
        self.db = db_session
        self.llm = llm_interface or LLMInterface()
        self.tester = tester
        self.mode = os.getenv("GUARDIAN_MODE", "semi_auto")
        self.auto_fix_enabled = os.getenv("GUARDIAN_AUTO_FIX", "true").lower() == "true"
        
    async def classify_issue(self, issue: Dict[str, Any]) -> ChangeType:
        """
        تصنيف المشكلة لتحديد نوع الإصلاح المطلوب
        """
        description = issue.get("description", "").lower()
        issue_type = issue.get("type", "").lower()
        
        # قواعد التصنيف
        if "crash" in description or "error" in issue_type:
            return ChangeType.HOTFIX
        elif "performance" in description or "slow" in description:
            return ChangeType.OPTIMIZATION
        elif "parameter" in description or "tune" in description:
            return ChangeType.PARAMETER_TUNING
        elif "logic" in issue_type or "algorithm" in description:
            return ChangeType.LOGIC_CHANGE
        else:
            return ChangeType.OPTIMIZATION
            
    async def generate_fix(self, issue: Dict[str, Any], original_code: str) -> Optional[CodeChange]:
        """
        توليد إصلاح للمشكلة
        """
        change_type = await self.classify_issue(issue)
        
        # طلب الإصلاح من LLM
        response = await self.llm.generate_fix(
            code=original_code,
            issue_description=issue["description"],
            constraints=[
                "حافظ على وظائف الكود الأساسية",
                "لا تغير الـ API العام",
                "أضف تعليقات توضيحية"
            ]
        )
        
        if not response.get("success"):
            logger.error(f"فشل في توليد الإصلاح: {response.get('error')}")
            return None
            
        data = response.get("data", {})
        
        change = CodeChange(
            change_type=change_type,
            status=ChangeStatus.PENDING,
            file_path=issue.get("file", "unknown"),
            original_code=original_code,
            proposed_code=data.get("fixed_code", ""),
            description=issue["description"],
            reasoning=data.get("explanation", ""),
        )
        
        # حفظ في قاعدة البيانات
        db_change = CodeChangeDB(**change.dict())
        self.db.add(db_change)
        self.db.commit()
        self.db.refresh(db_change)
        change.id = db_change.id
        
        logger.info(f"✅ تم توليد إصلاح #{change.id} من نوع {change_type.value}")
        return change
        
    async def apply_fix(self, change_id: int, force: bool = False) -> bool:
        """
        تطبيق إصلاح
        """
        db_change = self.db.query(CodeChangeDB).filter(
            CodeChangeDB.id == change_id
        ).first()
        
        if not db_change:
            logger.error(f"الإصلاح #{change_id} غير موجود")
            return False
            
        # التحقق من مستوى الموافقة
        approval_level = self.APPROVAL_MAP.get(db_change.change_type, ApprovalLevel.MANUAL)
        
        if approval_level == ApprovalLevel.MANUAL and not force:
            logger.warning(f"الإصلاح #{change_id} يتطلب موافقة يدوية")
            db_change.status = ChangeStatus.PENDING
            self.db.commit()
            return False
            
        if approval_level == ApprovalLevel.SEMI_AUTO and self.mode == "suggest_only" and not force:
            logger.info(f"الإصلاح #{change_id} في وضع الاقتراح فقط")
            return False
            
        # اختبار قبل التطبيق
        if self.tester:
            test_passed = await self.tester.validate_performance(
                db_change.proposed_code,
                db_change.file_path
            )
            if not test_passed:
                logger.error(f"فشل الاختبار للإصلاح #{change_id}")
                return False
                
        # تطبيق الإصلاح
        try:
            # TODO: كتابة الكود المصحح للملف
            # مع أخذ نسخة احتياطية
            
            db_change.status = ChangeStatus.DEPLOYED
            db_change.deployed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"🚀 تم تطبيق الإصلاح #{change_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تطبيق الإصلاح #{change_id}: {e}")
            await self.rollback_if_needed(change_id)
            return False
            
    async def rollback_if_needed(self, change_id: int, reason: str = ""):
        """
        التراجع عن إصلاح إذا لزم الأمر
        """
        db_change = self.db.query(CodeChangeDB).filter(
            CodeChangeDB.id == change_id
        ).first()
        
        if not db_change:
            return
            
        try:
            # TODO: استعادة النسخة الاحتياطية
            
            db_change.status = ChangeStatus.ROLLED_BACK
            db_change.rollback_reason = reason
            self.db.commit()
            
            logger.warning(f"⏪ تم التراجع عن الإصلاح #{change_id}: {reason}")
            
        except Exception as e:
            logger.error(f"فشل في التراجع عن الإصلاح #{change_id}: {e}")
            
    def get_pending_changes(self) -> List[CodeChange]:
        """الحصول على التغييرات المعلقة"""
        changes = self.db.query(CodeChangeDB).filter(
            CodeChangeDB.status == ChangeStatus.PENDING
        ).order_by(CodeChangeDB.created_at.desc()).all()
        
        return [CodeChange.from_orm(c) for c in changes]
        
    async def approve_change(self, change_id: int, approved_by: str):
        """الموافقة على تغيير يدوياً"""
        db_change = self.db.query(CodeChangeDB).filter(
            CodeChangeDB.id == change_id
        ).first()
        
        if db_change:
            db_change.status = ChangeStatus.APPROVED
            db_change.approved_by = approved_by
            db_change.approved_at = datetime.utcnow()
            self.db.commit()
            
            # تطبيق تلقائي بعد الموافقة
            await self.apply_fix(change_id, force=True)
            
    async def reject_change(self, change_id: int):
        """رفض تغيير"""
        db_change = self.db.query(CodeChangeDB).filter(
            CodeChangeDB.id == change_id
        ).first()
        
        if db_change:
            db_change.status = ChangeStatus.REJECTED
            self.db.commit()
