from fastapi import APIRouter

from .auth import router as auth_router
from .trading import router as trading_router
from .ai import router as ai_router
from .guardian import router as guardian_router
from .webhooks import router as webhooks_router
from .adaptive import router as adaptive_router
from .admin_settings import router as admin_settings_router
from .candles import router as candles_router
from .scanner import router as scanner_router
from .admin import router as admin_router
from .execution_from_signal import router as scanner_exec_router
from .predictive import router as predictive_router
from .execution import router as execution_router
from .market_data import router as market_data_router
from .mt5 import router as mt5_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(trading_router, prefix="/trading", tags=["trading"])
api_router.include_router(adaptive_router, prefix="/adaptive", tags=["adaptive"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(guardian_router, prefix="/guardian", tags=["guardian"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_settings_router, prefix="/admin/settings", tags=["admin"])

api_router.include_router(candles_router, prefix="/candles", tags=["candles"])
api_router.include_router(scanner_router, prefix="/scanner", tags=["scanner"])
api_router.include_router(scanner_exec_router)

api_router.include_router(predictive_router, prefix="/predictive", tags=["predictive"])
api_router.include_router(execution_router, prefix="/execution", tags=["execution"])

# MT5 connections management (used by frontend /dashboard/mt5)
api_router.include_router(mt5_router)

# Frontend expects /api/market-data/* (proxied to /api/v1/market-data/*)
api_router.include_router(market_data_router, prefix="/market-data", tags=["market-data"])