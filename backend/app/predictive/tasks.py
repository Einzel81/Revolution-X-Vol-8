from app.services.notification_service import celery_app
from app.database.connection import get_db
from app.predictive.service import PredictiveService

service = PredictiveService()

@celery_app.task(bind=True)
def predictive_run(symbol: str = "XAUUSD", timeframe: str = "M15"):
    import asyncio

    async def _run():
        async for db in get_db():
            return await service.run_full_report(db, symbol, timeframe)

    return asyncio.run(_run())