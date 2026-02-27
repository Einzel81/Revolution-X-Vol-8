"""
Code Analyzer - محلل الكود
تحليل الكود باستخدام LLM لاكتشاف المشاكل والاقتراحات
"""

import os
import ast
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from .llm_interface import LLMInterface
from .models import AnalysisResult, CodeChange, ChangeType, ChangeStatus

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """
    محلل الكود الذكي - يفحص الكود ويقتربح تحسينات
    """
    
    def __init__(self, db_session: Session, llm_interface: Optional[LLMInterface] = None):
        self.db = db_session
        self.llm = llm_interface or LLMInterface()
        self.project_root = Path(os.getenv("PROJECT_ROOT", "."))
        
    async def analyze_strategy(self, strategy_file: str) -> AnalysisResult:
        """
        تحليل ملف استراتيجية تداول كامل
        """
        file_path = self.project_root / strategy_file
        
        if not file_path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {strategy_file}")
            
        code = file_path.read_text(encoding='utf-8')
        
        # تحليلات متعددة
        issues = []
        
        # 1. تحليل ساكن (Static Analysis)
        static_issues = await self._static_analysis(code)
        issues.extend(static_issues)
        
        # 2. تحليل LLM
        if os.getenv("GUARDIAN_LLM_ENABLED", "true").lower() == "true":
            llm_analysis = await self.llm.analyze_code(
                code=code,
                context=f"ملف استراتيجية: {strategy_file}",
                analysis_type="trading_strategy"
            )
            
            if llm_analysis.get("success"):
                llm_issues = llm_analysis.get("data", {}).get("issues", [])
                issues.extend(self._normalize_llm_issues(llm_issues))
                
        # 3. فحص اختلاف الباك-تست
        backtest_issues = await self._check_backtest_divergence(strategy_file)
        issues.extend(backtest_issues)
        
        return AnalysisResult(
            issues_found=issues,
            suggestions=self._extract_suggestions(issues),
            confidence_score=self._calculate_confidence(issues),
            analyzed_files=[strategy_file]
        )
        
    async def _static_analysis(self, code: str) -> List[Dict[str, Any]]:
        """التحليل الساكن للكود"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # فحص الاستثناءات الفارغة
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.body and len(node.body) == 1:
                        if isinstance(node.body[0], ast.Pass):
                            issues.append({
                                "type": "security",
                                "severity": "high",
                                "line": node.lineno,
                                "description": "استثناء فارغ (pass) - قد يخفي أخطاء",
                                "suggestion": "أضف تسجيل للخطأ أو معالجة مناسبة"
                            })
                            
                # فحص المتغيرات غير المستخدمة
                if isinstance(node, ast.Name):
                    # TODO: تحليل أكثر تعقيداً للمتغيرات
                    pass
                    
        except SyntaxError as e:
            issues.append({
                "type": "logic",
                "severity": "critical",
                "line": e.lineno,
                "description": f"خطأ في بناء الجملة: {e.msg}",
                "suggestion": "صحح الخطأ النحوي"
            })
            
        return issues
        
    def _normalize_llm_issues(self, llm_issues: List[Dict]) -> List[Dict[str, Any]]:
        """توحيد تنسيق المشاكل القادمة من LLM"""
        normalized = []
        for issue in llm_issues:
            normalized.append({
                "type": issue.get("type", "general"),
                "severity": issue.get("severity", "medium"),
                "line": issue.get("line", 0),
                "description": issue.get("description", ""),
                "suggestion": issue.get("suggestion", ""),
                "source": "llm"
            })
        return normalized
        
    async def _check_backtest_divergence(self, strategy_file: str) -> List[Dict[str, Any]]:
        """
        فحص اختلاف نتائج الباك-تست عن التداول الحي
        """
        issues = []
        
        # TODO: مقارنة نتائج الباك-تست مع الليف
        # هذا يتطلب الوصول لسجلات التداول
        
        return issues
        
    def _extract_suggestions(self, issues: List[Dict]) -> List[Dict[str, Any]]:
        """استخراج الاقتراحات من المشاكل"""
        suggestions = []
        for issue in issues:
            if issue.get("suggestion"):
                suggestions.append({
                    "description": issue["suggestion"],
                    "priority": issue.get("severity", "medium"),
                    "related_issue": issue.get("description", "")
                })
        return suggestions
        
    def _calculate_confidence(self, issues: List[Dict]) -> float:
        """حساب درجة الثقة في التحليل"""
        if not issues:
            return 95.0
            
        # حساب بناءً على عدد المشاكل وأنواعها
        critical = sum(1 for i in issues if i.get("severity") == "critical")
        high = sum(1 for i in issues if i.get("severity") == "high")
        
        if critical > 0:
            return 30.0
        elif high > 2:
            return 50.0
        else:
            return 80.0
            
    async def detect_bugs(self, file_pattern: str = "*.py") -> List[Dict[str, Any]]:
        """
        اكتشاف الأخطاء في مجموعة ملفات
        """
        bugs = []
        files = list(self.project_root.rglob(file_pattern))
        
        for file_path in files:
            try:
                code = file_path.read_text(encoding='utf-8')
                # فحوصات سريعة للأخطاء الشائعة
                if "except:" in code and "Exception" not in code:
                    bugs.append({
                        "file": str(file_path),
                        "type": "bare_except",
                        "severity": "high",
                        "description": "استخدام bare except يمكن أن يخفي KeyboardInterrupt"
                    })
            except Exception as e:
                logger.error(f"خطأ في قراءة {file_path}: {e}")
                
        return bugs
        
    async def suggest_improvements(self, target_module: str) -> List[CodeChange]:
        """
        اقتراح تحسينات على وحدة معينة
        """
        changes = []
        
        # تحليل الوحدة
        result = await self.analyze_strategy(target_module)
        
        for issue in result.issues_found:
            if issue.get("severity") in ["high", "critical"]:
                # إنشاء تغيير مقترح
                change = CodeChange(
                    change_type=ChangeType.HOTFIX if issue["type"] == "logic" else ChangeType.OPTIMIZATION,
                    status=ChangeStatus.PENDING,
                    file_path=target_module,
                    original_code="",  # TODO: استخراج الكود الأصلي
                    proposed_code="",  # TODO: توليد الإصلاح
                    description=issue["description"],
                    reasoning=issue.get("suggestion", "")
                )
                changes.append(change)
                
        return changes
        
    async def analyze_performance_bottlenecks(self, code: str) -> List[Dict[str, Any]]:
        """
        تحليل اختناقات الأداء
        """
        bottlenecks = []
        
        # فحص الحلقات المتداخلة
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.For):
                    # فحص إذا كانت الحلقة داخل حلقة أخرى
                    for child in ast.walk(node):
                        if isinstance(child, ast.For) and child != node:
                            bottlenecks.append({
                                "type": "nested_loop",
                                "line": child.lineno,
                                "severity": "medium",
                                "description": "حلقة متداخلة قد تؤثر على الأداء",
                                "suggestion": "استخدم vectorization أو تحسين الخوارزمية"
                            })
        except:
            pass
            
        return bottlenecks
