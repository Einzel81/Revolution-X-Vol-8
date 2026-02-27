from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    # Import ALL models so create_all picks them up.
    # (This project currently uses create_all; migrations can be added later via Alembic.)
    from app.models import user  # noqa: F401
    from app.models import trade  # noqa: F401
    from app.models import alert  # noqa: F401
    from app.models import notification  # noqa: F401
    from app.models import telegram_user  # noqa: F401
    from app.models import execution_event  # noqa: F401
    from app.models import execution_log  # noqa: F401
    from app.models import mt5_position_snapshot  # noqa: F401
    from app.models import candle  # noqa: F401
    from app.models import trading_signal  # noqa: F401
    from app.models import app_setting  # noqa: F401
    from app.models import model_registry  # noqa: F401
    from app.models import model_training_run  # noqa: F401
    from app.models import predictive_report  # noqa: F401

    async with engine.begin() as conn:
        # Ensure TimescaleDB extension exists (safe no-op if already enabled).
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))

        await conn.run_sync(Base.metadata.create_all)

        # Convert time-series tables to hypertables (safe if already hypertable).
        await conn.execute(
            text("SELECT create_hypertable('candles', 'time', if_not_exists => TRUE);")
        )


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session