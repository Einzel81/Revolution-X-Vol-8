"""
LLM Interface - واجهة نماذج اللغة الكبيرة
للتواصل مع GPT-4 و Claude
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
import openai
import anthropic

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    GPT4 = "gpt4"
    CLAUDE = "claude"

class LLMInterface:
    """
    واجهة موحدة للتعامل مع نماذج اللغة المختلفة
    """
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or LLMProvider(
            os.getenv("GUARDIAN_LLM_PROVIDER", "gpt4")
        )
        
        # تهيئة العملاء
        self.openai_client = None
        self.anthropic_client = None
        
        if self.provider == LLMProvider.GPT4:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY غير محدد")
            self.openai_client = openai.AsyncOpenAI(api_key=api_key)
            
        elif self.provider == LLMProvider.CLAUDE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY غير محدد")
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
            
    async def query(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        إرسال استعلام للنموذج
        
        Args:
            prompt: نص الاستعلام
            system_prompt: تعليمات النظام
            temperature: درجة الإبداع (0-1)
            max_tokens: الحد الأقصى للرموز
            json_mode: هل نريد إخراج JSON
            
        Returns:
            الرد المفحوص
        """
        if self.provider == LLMProvider.GPT4:
            return await self._query_gpt4(
                prompt, system_prompt, temperature, max_tokens, json_mode
            )
        else:
            return await self._query_claude(
                prompt, system_prompt, temperature, max_tokens
            )
            
    async def _query_gpt4(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> Dict[str, Any]:
        """الاستعلام من GPT-4"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else None
            )
            
            content = response.choices[0].message.content
            return {
                "success": True,
                "content": content,
                "model": "gpt-4-turbo-preview",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"خطأ في GPT-4: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
            
    async def _query_claude(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """الاستعلام من Claude 3"""
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return {
                "success": True,
                "content": content,
                "model": "claude-3-opus-20240229",
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"خطأ في Claude: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
            
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        فحص وتحليل رد النموذج
        """
        if not response.get("success"):
            return {
                "success": False,
                "error": response.get("error"),
                "data": None
            }
            
        content = response.get("content", "")
        
        # محاولة تحليل JSON
        try:
            data = json.loads(content)
            return {
                "success": True,
                "data": data,
                "raw": content
            }
        except json.JSONDecodeError:
            # إرجاع النص كما هو
            return {
                "success": True,
                "data": {"analysis": content},
                "raw": content
            }
            
    async def analyze_code(
        self,
        code: str,
        context: Optional[str] = None,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """
        تحليل كود باستخدام LLM
        """
        system_prompt = """أنت خبير في تحليل كود Python للتداول الآلي. 
        قم بتحليل الكود المقدم واكتشف:
        1. الأخطاء المنطقية والبرمجية
        2. حالات الحافة (Edge Cases) غير المغطاة
        3. فرص التحسين في الأداء
        4. مشاكل الأمان المحتملة
        
        قدم الإجابة بتنسيق JSON فقط."""
        
        prompt = f"""
        نوع التحليل: {analysis_type}
        
        الكود:
        ```python
        {code}
        ```
        
        السياق: {context or 'لا يوجد'}
        
        قدم تحليلاً مفصلاً يحتوي على:
        {{
            "issues": [
                {{
                    "type": "logic|performance|security|edge_case",
                    "severity": "high|medium|low",
                    "line": رقم_السطر,
                    "description": "وصف المشكلة",
                    "suggestion": "كيفية الإصلاح"
                }}
            ],
            "optimizations": [
                {{
                    "description": "وصف التحسين",
                    "impact": "high|medium|low",
                    "effort": "easy|medium|hard"
                }}
            ],
            "overall_score": 0-100
        }}
        """
        
        response = await self.query(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True
        )
        
        return self.parse_response(response)
        
    async def generate_fix(
        self,
        code: str,
        issue_description: str,
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        توليد إصلاح للكود
        """
        system_prompt = """أنت مطور Python خبير. قم بإصلاح الكود بناءً على الوصف المقدم.
        حافظ على أسلوب الكود الأصلي وأضف تعليقات توضيحية."""
        
        constraints_text = "\n".join([f"- {c}" for c in (constraints or [])])
        
        prompt = f"""
        الكود الأصلي:
        ```python
        {code}
        ```
        
        المشكلة: {issue_description}
        
        القيود:
        {constraints_text}
        
        قدم الإصلاح بتنسيق JSON:
        {{
            "fixed_code": "الكود المصحح كاملاً",
            "changes_made": ["قائمة التغييرات"],
            "explanation": "شرح الإصلاح",
            "confidence": 0-100
        }}
        """
        
        response = await self.query(
            prompt=prompt,
            system_prompt=system_prompt,
            json_mode=True
        )
        
        return self.parse_response(response)
