# backend/app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1 import trading, websocket

api_router = APIRouter()

api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
# websocket handled in main.py
