# backend/app/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings  # ???? ?? ??? ?? ??? settings ??????? ???? ???????
from app.api.v1.router import api_router
from app.database.connection import init_db
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    setup_logging()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Revolution X API",
    description="AI-Powered Gold Trading System",
    version="1.0.0",
    lifespan=lifespan,
)

# -----------------------------
# CORS (Fix: explicit origins)
# -----------------------------
allowed_origins = list(getattr(settings, "ALLOWED_HOSTS", []) or [])

# ??? ????? Origin ??????? ??? ??????? (????? ??????? ??? CORS ????)
allowed_origins += [
    "http://142.93.95.110:3000",
    "https://142.93.95.110:3000",
    "http://142.93.95.110",
    "https://142.93.95.110",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ????? ??????? + ?????
allowed_origins = sorted(set([o.strip() for o in allowed_origins if isinstance(o, str) and o.strip()]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "revolution-x"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
        except Exception:
            break