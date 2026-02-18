"""
AI Code Guardian - Code Analyzer
محلل الكود الذكي باستخدام LLM
"""

import ast
import inspect
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

class IssueType(Enum):
    LOGIC_ERROR = "logic_error"
    EDGE_CASE = "edge_case"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    BACKTEST_DIVERGENCE = "backtest_divergence"
    CODE_SMELL = "code_smell"

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CodeIssue:
    id: str
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: Severity
    description: str
    code_snippet: str
    suggested_fix: str
    confidence: float  # 0-1
    auto_fixable: bool

@dataclass
class AnalysisReport:
    timestamp: str
    files_analyzed: int
    issues_found: int
    critical_issues: int
    issues: List[CodeIssue]
    summary: str
    recommendations: List[str]

class CodeAnalyzer:
    """
    محلل الكود المتقدم للكشف عن المشاكل والثغرات
    """
    
    def __init__(self, llm_interface=None):
        self.llm = llm_interface
        self.issue_patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict[str, Any]:
        """تحميل أنماط المشاكل المعروفة"""
        return {
            'division_by_zero': r'/\s*\w+\s*(?![+\-*/])',
            'bare_except': r'except\s*:',
            'hardcoded_secrets': r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
            'infinite_loop': r'while\s+True\s*:',
            'recursive_without_base': r'def\s+(\w+).*?\1\(',
            'magic_numbers': r'[^\'"\w](\d{3,})[^\'"\w]'
        }
    
    async def analyze_strategy(self, strategy_code: str, 
                              strategy_name: str = "unknown") -> AnalysisReport:
        """
        تحليل استراتيجية تداول كاملة
        """
        issues = []
        
        # 1. تحليل ساكن (Static Analysis)
        static_issues = await self._static_analysis(strategy_code, strategy_name)
        issues.extend(static_issues)
        
        # 2. تحليل منطقي باستخدام LLM
        if self.llm:
            llm_issues = await self._llm_analysis(strategy_code, strategy_name)
            issues.extend(llm_issues)
        
        # 3. فحص Edge Cases
        edge_cases = await self._detect_edge_cases(strategy_code, strategy_name)
        issues.extend(edge_cases)
        
        # 4. فحص الأمان
        security_issues = await self._security_scan(strategy_code, strategy_name)
        issues.extend(security_issues)
        
        critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        
        return AnalysisReport(
            timestamp=datetime.utcnow().isoformat(),
            files_analyzed=1,
            issues_found=len(issues),
            critical_issues=critical_count,
            issues=issues,
            summary=self._generate_summary(issues),
            recommendations=self._generate_recommendations(issues)
        )
    
    async def _static_analysis(self, code: str, filename: str) -> List[CodeIssue]:
        """التحليل الساكن للكود"""
        issues = []
        lines = code.split('\n')
        
        try:
            tree = ast.parse(code)
            
            # فحص الاستيرادات غير المستخدمة
            imported = set()
            used = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imported.add(node.module)
                elif isinstance(node, ast.Name):
                    used.add(node.id)
            
            unused = imported - used
            for imp in unused:
                issues.append(CodeIssue(
                    id=f"unused_import_{imp}",
                    file_path=filename,
                    line_number=0,
                    issue_type=IssueType.CODE_SMELL,
                    severity=Severity.LOW,
                    description=f"استيراد غير مستخدم: {imp}",
                    code_snippet=f"import {imp}",
                    suggested_fix=f"إزالة 'import {imp}'",
                    confidence=0.9,
                    auto_fixable=True
                ))
            
            # فحص الـ except العاري
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        issues.append(CodeIssue(
                            id=f"bare_except_{node.lineno}",
                            file_path=filename,
                            line_number=node.lineno,
                            issue_type=IssueType.SECURITY,
                            severity=Severity.HIGH,
                            description="استخدام except: عاري يمكن أن يخفي أخطاء خطيرة",
                            code_snippet=lines[node.lineno-1].strip(),
                            suggested_fix="استخدام 'except SpecificException:'",
                            confidence=0.95,
                            auto_fixable=False
                        ))
            
            # فحص المتغيرات غير المستخدمة
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            # التحقق إذا كان يستخدم لاحقاً
                            if not self._is_variable_used(tree, target.id):
                                issues.append(CodeIssue(
                                    id=f"unused_var_{target.lineno}",
                                    file_path=filename,
                                    line_number=target.lineno,
                                    issue_type=IssueType.CODE_SMELL,
                                    severity=Severity.LOW,
                                    description=f"متغير غير مستخدم: {target.id}",
                                    code_snippet=lines[target.lineno-1].strip(),
                                    suggested_fix=f"إزالة المتغير '{target.id}' أو استخدامه",
                                    confidence=0.8,
                                    auto_fixable=True
                                ))
        
        except SyntaxError as e:
            issues.append(CodeIssue(
                id=f"syntax_error_{e.lineno}",
                file_path=filename,
                line_number=e.lineno or 0,
                issue_type=IssueType.LOGIC_ERROR,
                severity=Severity.CRITICAL,
                description=f"خطأ نحوي: {e.msg}",
                code_snippet=lines[e.lineno-1] if e.lineno else "",
                suggested_fix="تصحيح الخطأ النحوي",
                confidence=1.0,
                auto_fixable=False
            ))
        
        return issues
    
    def _is_variable_used(self, tree: ast.AST, var_name: str) -> bool:
        """التحقق إذا كان المتغير مستخدماً"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == var_name:
                if isinstance(node.ctx, ast.Load):
                    return True
        return False
    
    async def _llm_analysis(self, code: str, filename: str) -> List[CodeIssue]:
        """التحليل باستخدام LLM"""
        if not self.llm:
            return []
        
        prompt = f"""Analyze this trading bot code for issues:

File: {filename}

```python
{code[:4000]}  # Limit for token economy
