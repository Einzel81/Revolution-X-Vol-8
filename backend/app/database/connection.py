from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def _safe_exec(conn, sql: str) -> None:
    """Execute SQL and never fail startup.

    Timescale operations can fail due to schema constraints (PK/UNIQUE rules) or
    if a policy already exists. We prefer a running API with tables created.
    """
    try:
        await conn.execute(text(sql))
    except Exception:
        # Intentionally swallow errors: DB initialization must not crash the API.
        return


async def init_db() -> None:
    """Initialize DB schema and enforce TimescaleDB best practices.

    - Ensures TimescaleDB extension exists.
    - Creates SQLAlchemy tables.
    - Converts selected tables to hypertables.

    Important: we DO NOT convert transactional tables (e.g., trades) to hypertables
    because they are referenced by FK constraints and usually use UUID PKs.
    """

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

    # 1) Create extensions + tables in a clean transaction
    async with engine.begin() as conn:
        await _safe_exec(conn, "CREATE EXTENSION IF NOT EXISTS timescaledb")
        await _safe_exec(conn, "CREATE EXTENSION IF NOT EXISTS pgcrypto")
        await conn.run_sync(Base.metadata.create_all)

    # 2) Timescale hardening in a separate transaction.
    # If any hypertable op fails, we still keep the tables from step (1).
    async with engine.begin() as conn:
        # Hypertables (time-series only)
        await _safe_exec(conn, "SELECT create_hypertable('candles', 'time', if_not_exists => TRUE);")
        await _safe_exec(conn, "SELECT create_hypertable('execution_events', 'created_at', if_not_exists => TRUE);")
        await _safe_exec(conn, "SELECT create_hypertable('execution_logs', 'created_at', if_not_exists => TRUE);")
        await _safe_exec(conn, "SELECT create_hypertable('trading_signals', 'created_at', if_not_exists => TRUE);")
        await _safe_exec(conn, "SELECT create_hypertable('mt5_position_snapshots', 'created_at', if_not_exists => TRUE);")
        await _safe_exec(conn, "SELECT create_hypertable('predictive_reports', 'created_at', if_not_exists => TRUE);")

        # Indexes (idempotent)
        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_execution_events_created_at_desc ON execution_events (created_at DESC);")
        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_execution_events_symbol_created_at ON execution_events (symbol, created_at DESC);")
        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_execution_events_user_created_at ON execution_events (user_id, created_at DESC);")

        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_execution_logs_trade_created_at ON execution_logs (trade_id, created_at DESC);")
        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_execution_logs_created_at_desc ON execution_logs (created_at DESC);")

        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_trading_signals_user_created_at ON trading_signals (user_id, created_at DESC);")
        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_trading_signals_symbol_tf_created_at ON trading_signals (symbol, timeframe, created_at DESC);")

        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_mt5_pos_account_created_at ON mt5_position_snapshots (account_id, created_at DESC);")
        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_mt5_pos_symbol_created_at ON mt5_position_snapshots (symbol, created_at DESC);")

        await _safe_exec(conn, "CREATE INDEX IF NOT EXISTS ix_predictive_symbol_tf_created_at ON predictive_reports (symbol, timeframe, created_at DESC);")

        # Retention policies (best-effort, idempotent)
        await _safe_exec(
            conn,
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
            """,
        )


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session