# backend/app/celery_app.py
from __future__ import annotations

from celery import Celery

celery_app = Celery(
    "revolutionx",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    # ? ??? ????? ?? ???????: ????? tasks ??? ?? autodiscover ???
    imports=("app.tasks.market_tasks",),
)

# ? ???? Beat
celery_app.conf.beat_schedule = {
    "ingest-and-scan-every-minute": {
        "task": "app.tasks.market_tasks.ingest_and_scan",
        "schedule": 60.0,
        "args": (),
        "kwargs": {},
    }
}