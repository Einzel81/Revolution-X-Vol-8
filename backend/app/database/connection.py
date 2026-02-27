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

        # ------------------------------------------------------------------
        # TimescaleDB hardening (Step 5)
        # - Convert core time-series tables to hypertables
        # - Add critical indexes
        # - Add retention policies (best-effort, idempotent)
        #
        # This runs AFTER create_all, so it's the reliable place to enforce
        # hypertables even when init-scripts ran before tables existed.
        # ------------------------------------------------------------------

        # Hypertables
        await conn.execute(text("SELECT create_hypertable('candles', 'time', if_not_exists => TRUE);"))
        await conn.execute(text("SELECT create_hypertable('execution_events', 'created_at', if_not_exists => TRUE);"))
        await conn.execute(text("SELECT create_hypertable('execution_logs', 'created_at', if_not_exists => TRUE);"))
        await conn.execute(text("SELECT create_hypertable('trading_signals', 'created_at', if_not_exists => TRUE);"))
        await conn.execute(text("SELECT create_hypertable('trades', 'created_at', if_not_exists => TRUE);"))
        await conn.execute(text("SELECT create_hypertable('mt5_position_snapshots', 'created_at', if_not_exists => TRUE);"))
        await conn.execute(text("SELECT create_hypertable('predictive_reports', 'created_at', if_not_exists => TRUE);"))

        # Indexes (idempotent)
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_execution_events_created_at_desc ON execution_events (created_at DESC);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_execution_events_symbol_created_at ON execution_events (symbol, created_at DESC);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_execution_events_user_created_at ON execution_events (user_id, created_at DESC);"))

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_execution_logs_trade_created_at ON execution_logs (trade_id, created_at DESC);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_execution_logs_created_at_desc ON execution_logs (created_at DESC);"))

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_trading_signals_user_created_at ON trading_signals (user_id, created_at DESC);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_trading_signals_symbol_tf_created_at ON trading_signals (symbol, timeframe, created_at DESC);"))

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_trades_user_open_time ON trades (user_id, open_time DESC);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_trades_symbol_open_time ON trades (symbol, open_time DESC);"))

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_mt5_pos_account_created_at ON mt5_position_snapshots (account_id, created_at DESC);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_mt5_pos_symbol_created_at ON mt5_position_snapshots (symbol, created_at DESC);"))

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_predictive_symbol_tf_created_at ON predictive_reports (symbol, timeframe, created_at DESC);"))

        # Retention policies (best-effort, idempotent)
        # Timescale will error if a policy already exists; we swallow that.
        # If add_retention_policy is not available, swallow as well.
        await conn.execute(
            text(
                """
DO $$
BEGIN
  BEGIN PERFORM add_retention_policy('candles', INTERVAL '365 days'); EXCEPTION WHEN OTHERS THEN NULL; END;
  BEGIN PERFORM add_retention_policy('execution_events', INTERVAL '180 days'); EXCEPTION WHEN OTHERS THEN NULL; END;
  BEGIN PERFORM add_retention_policy('execution_logs', INTERVAL '180 days'); EXCEPTION WHEN OTHERS THEN NULL; END;
  BEGIN PERFORM add_retention_policy('trading_signals', INTERVAL '365 days'); EXCEPTION WHEN OTHERS THEN NULL; END;
  BEGIN PERFORM add_retention_policy('mt5_position_snapshots', INTERVAL '30 days'); EXCEPTION WHEN OTHERS THEN NULL; END;
  BEGIN PERFORM add_retention_policy('predictive_reports', INTERVAL '730 days'); EXCEPTION WHEN OTHERS THEN NULL; END;
END $$;
                """
            )
        )


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session