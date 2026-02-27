"""
Revolution X Trading Bot - Main Entry Point
النقطة الرئيسية لتشغيل البوت
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.logging import setup_logging

# API Routes
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.trading import router as trading_router
from app.api.v1.ai import router as ai_router
from app.api.v1.guardian import router as guardian_router

# Services
from app.services.trading_engine import TradingEngine
from app.services.risk_manager import RiskManager

# AI Guardian
from app.guardian.monitor import PerformanceMonitor
from app.guardian.analyzer import CodeAnalyzer
from app.guardian.fixer import AutoFixer
from app.guardian.tester import SafeTester
from app.guardian.deployer import SmartDeployer
from app.guardian.knowledge_base import KnowledgeBase
from app.guardian.llm_interface import LLMInterface

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global instances
trading_engine: TradingEngine = None
risk_manager: RiskManager = None
guardian_monitor: PerformanceMonitor = None
guardian_analyzer: CodeAnalyzer = None
guardian_fixer: AutoFixer = None

async def init_guardian(db):
    """
    تهيئة AI Code Guardian
    """
    global guardian_monitor, guardian_analyzer, guardian_fixer
    
    if not settings.GUARDIAN_ENABLED:
        logger.info("⏸️ AI Code Guardian معطل")
        return
        
    logger.info("🤖 تهيئة AI Code Guardian...")
    
    try:
        # تهيئة LLM
        llm = LLMInterface()
        
        # تهيئة المكونات
        guardian_monitor = PerformanceMonitor(db)
        guardian_analyzer = CodeAnalyzer(db, llm)
        tester = SafeTester(db)
        guardian_fixer = AutoFixer(db, llm, tester)
        
        # تسجيل معالج التنبيهات
        async def on_alert(alert):
            """معالج التنبيهات التلقائي"""
            logger.warning(f"🚨 تنبيه Guardian: {alert.message}")
            
            # محاولة إصلاح تلقائي للمشاكل الحرجة
            if alert.severity == "critical" and settings.GUARDIAN_AUTO_FIX:
                logger.info("🔧 محاولة إصلاح تلقائي...")
                # TODO: تحديد الملف المتأثر وتوليد الإصلاح
                
        guardian_monitor.register_alert_handler(on_alert)
        
        # بدء المراقبة
        await guardian_monitor.start()
        
        # جدولة التحليل الدوري
        asyncio.create_task(scheduled_analysis(db))
        
        logger.info("✅ AI Code Guardian جاهز للعمل!")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تهيئة Guardian: {e}")

async def scheduled_analysis(db):
    """
    تحليل دوري للكود
    """
    while True:
        try:
            await asyncio.sleep(3600)  # كل ساعة
            
            if not settings.GUARDIAN_ENABLED:
                continue
                
            logger.info("🔍 بدء التحليل الدوري للكود...")
            
            # تحليل الملفات الرئيسية
            files_to_analyze = [
                "app/strategies/smc_strategy.py",
                "app/strategies/ai_strategy.py",
                "app/services/trading_engine.py",
                "app/services/risk_manager.py"
            ]
            
            for file_path in files_to_analyze:
                try:
                    result = await guardian_analyzer.analyze_strategy(file_path)
                    
                    if result.issues_found:
                        logger.warning(f"⚠️ تم العثور على {len(result.issues_found)} مشكلة في {file_path}")
                        
                        # توليد إصلاحات للمشاكل الحرجة
                        for issue in result.issues_found:
                            if issue.get("severity") in ["critical", "high"]:
                                await guardian_fixer.generate_fix(issue, "")
                                
                except Exception as e:
                    logger.error(f"خطأ في تحليل {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"خطأ في التحليل المجدول: {e}")

async def init_trading_engine(db):
    """
    تهيئة محرك التداول
    """
    global trading_engine, risk_manager
    
    logger.info("📈 تهيئة محرك التداول...")
    
    risk_manager = RiskManager(db)
    trading_engine = TradingEngine(db, risk_manager)
    
    # TODO: بدء المحرك إذا كان الوضع AUTO_START مفعل
    # await trading_engine.start()
    
    logger.info("✅ محرك التداول جاهز")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    إدارة دورة حياة التطبيق
    """
    logger.info("🚀 بدء تشغيل Revolution X...")
    
    # إنشاء الجداول
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # تهيئة الخدمات
        await init_trading_engine(db)
        await init_guardian(db)
        
        logger.info("✅ التطبيق جاهز للعمل!")
        yield
        
    finally:
        # إيقاف الخدمات
        logger.info("🛑 إيقاف الخدمات...")
        
        if guardian_monitor:
            await guardian_monitor.stop()
            
        if trading_engine:
            await trading_engine.stop()
            
        db.close()
        logger.info("👋 تم إيقاف التطبيق")

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="Revolution X Trading Bot",
    description="نظام تداول ذكي متكامل مع AI Code Guardian",
    version="5.9.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين الـ Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(trading_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(guardian_router, prefix="/api/v1")

@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "name": "Revolution X",
        "version": "5.9.0",
        "status": "operational",
        "features": [
            "SMC Trading",
            "AI Analysis",
            "Risk Management",
            "AI Code Guardian"
        ]
    }

@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    health = {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "up",
            "trading_engine": "up" if trading_engine else "down",
            "guardian": "up" if guardian_monitor and guardian_monitor.is_running else "down"
        }
    }
    
    # التحقق من حالة Guardian
    if settings.GUARDIAN_ENABLED:
        health["guardian_status"] = {
            "enabled": True,
            "monitoring": guardian_monitor.is_running if guardian_monitor else False,
            "mode": settings.GUARDIAN_MODE,
            "llm_provider": settings.GUARDIAN_LLM_PROVIDER
        }
    
    return health

@app.get("/api/v1/system/status")
async def system_status():
    """حالة النظام الكاملة"""
    db = SessionLocal()
    
    try:
        from app.guardian.knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(db)
        trends = kb.get_performance_trends()
        
        return {
            "trading_engine": {
                "status": "running" if trading_engine else "stopped",
                "active_positions": 0,  # TODO: من TradingEngine
                "daily_pnl": 0.0
            },
            "guardian": {
                "enabled": settings.GUARDIAN_ENABLED,
                "monitoring": guardian_monitor.is_running if guardian_monitor else False,
                "pending_changes": len(guardian_fixer.get_pending_changes()) if guardian_fixer else 0,
                "active_alerts": len(guardian_monitor.get_active_alerts()) if guardian_monitor else 0
            },
            "performance": trends,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
