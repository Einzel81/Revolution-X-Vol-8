from __future__ import annotations

import asyncio
import contextlib
import json
import time
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.services.activity_bus import activity_bus


class WSManager:
    def __init__(self) -> None:
        self.clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self.clients.discard(ws)

    async def broadcast(self, message: dict) -> None:
        data = json.dumps(message, ensure_ascii=False)
        async with self._lock:
            clients = list(self.clients)

        if not clients:
            return

        dead = []
        for ws in clients:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self.clients.discard(ws)


ws_manager = WSManager()


async def _activity_forwarder() -> None:
    async for msg in activity_bus.listen():
        await ws_manager.broadcast(
            {
                "type": "activity",
                "payload": msg,
                "timestamp": int(time.time() * 1000),
            }
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_activity_forwarder())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(Exception):
            await task


app = FastAPI(title="Revolution X API", lifespan=lifespan)

# ? CORS ????? ??? Cookies
# ?? ???? "*" ?? allow_credentials=True ?? ???????.
ALLOWED_ORIGINS = [
    "http://142.93.95.110:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"ok": True}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            try:
                await ws.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                continue
    finally:
        await ws_manager.disconnect(ws)