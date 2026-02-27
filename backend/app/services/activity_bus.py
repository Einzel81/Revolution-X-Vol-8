from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Dict, Optional


class ActivityBus:
    """
    In-process activity bus (async queue) used to forward events to WebSocket clients.
    - publish(): push event
    - listen(): async generator yielding events
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=10_000)

    async def publish(self, payload: Dict[str, Any]) -> None:
        # ?? ???? ??? ?????? ?? ???? queue ??????
        try:
            self._queue.put_nowait(payload)
        except asyncio.QueueFull:
            # Drop oldest by draining 1 then push
            try:
                _ = self._queue.get_nowait()
            except Exception:
                pass
            try:
                self._queue.put_nowait(payload)
            except Exception:
                pass

    async def listen(self) -> AsyncIterator[Dict[str, Any]]:
        while True:
            msg = await self._queue.get()
            yield msg


# ? Singleton used by app
activity_bus = ActivityBus()

# ? Backwards-compatible API for existing imports
async def publish_activity(payload: Dict[str, Any]) -> None:
    await activity_bus.publish(payload)

# ??? ??????? ?? ?????? ??? ?????
async def publish(payload: Dict[str, Any]) -> None:
    await activity_bus.publish(payload)