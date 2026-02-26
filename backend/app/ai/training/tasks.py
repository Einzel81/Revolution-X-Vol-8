from app.services.notification_service import celery_app
from app.database.connection import get_db
from app.ai.training.trainers import train_xgb, train_lgbm
from app.ai.training.train_lstm import train_lstm

@celery_app.task(bind=True)
def train_models(symbol: str = "XAUUSD", timeframe: str = "M15"):
    import asyncio

    async def _run():
        async for db in get_db():
            r1 = await train_xgb(db, symbol, timeframe)
            r2 = await train_lgbm(db, symbol, timeframe)
            r3 = await train_lstm(db, symbol, timeframe)  # optional (skips if TF missing)
            return {"xgb": r1, "lgbm": r2, "lstm": r3}

    return asyncio.run(_run())