-- init-scripts/01-timescale.sql
-- Runs once on first database initialization (POSTGRES_DB=revolution_x)

-- TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Optional but useful extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Hypertables are created after SQLAlchemy creates the tables
-- (see backend/app/database/connection.py)

-- -------------------------------------------------------------------
-- Optional: Idempotent hypertables + indexes + retention policies
--
-- Note:
-- - This file runs on first DB init.
-- - Tables may be created later by the app (SQLAlchemy create_all).
-- - Therefore we guard each operation with to_regclass() checks.
-- - The app ALSO applies these at startup in backend/app/database/connection.py
--   to ensure hypertables/policies are enforced even if tables are created later.
-- -------------------------------------------------------------------

DO $$
BEGIN
  -- candles(time)
  IF to_regclass('public.candles') IS NOT NULL THEN
    PERFORM create_hypertable('candles', 'time', if_not_exists => TRUE);
  END IF;

  -- execution_events(created_at)
  IF to_regclass('public.execution_events') IS NOT NULL THEN
    PERFORM create_hypertable('execution_events', 'created_at', if_not_exists => TRUE);
  END IF;

  -- execution_logs(created_at)
  IF to_regclass('public.execution_logs') IS NOT NULL THEN
    PERFORM create_hypertable('execution_logs', 'created_at', if_not_exists => TRUE);
  END IF;

  -- trading_signals(created_at)
  IF to_regclass('public.trading_signals') IS NOT NULL THEN
    PERFORM create_hypertable('trading_signals', 'created_at', if_not_exists => TRUE);
  END IF;

  -- mt5_position_snapshots(created_at)
  IF to_regclass('public.mt5_position_snapshots') IS NOT NULL THEN
    PERFORM create_hypertable('mt5_position_snapshots', 'created_at', if_not_exists => TRUE);
  END IF;

  -- predictive_reports(created_at)
  IF to_regclass('public.predictive_reports') IS NOT NULL THEN
    PERFORM create_hypertable('predictive_reports', 'created_at', if_not_exists => TRUE);
  END IF;
END $$;

-- Indexes (idempotent)
CREATE INDEX IF NOT EXISTS ix_execution_events_created_at_desc ON execution_events (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_execution_events_symbol_created_at ON execution_events (symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_execution_events_user_created_at ON execution_events (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_execution_logs_trade_created_at ON execution_logs (trade_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_execution_logs_created_at_desc ON execution_logs (created_at DESC);

CREATE INDEX IF NOT EXISTS ix_trading_signals_user_created_at ON trading_signals (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_trading_signals_symbol_tf_created_at ON trading_signals (symbol, timeframe, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_mt5_pos_account_created_at ON mt5_position_snapshots (account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_mt5_pos_symbol_created_at ON mt5_position_snapshots (symbol, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_predictive_symbol_tf_created_at ON predictive_reports (symbol, timeframe, created_at DESC);

-- Retention policies (idempotent best-effort)
DO $$
BEGIN
  -- Keep candles for 365 days by default
  IF to_regclass('public.candles') IS NOT NULL THEN
    BEGIN
      PERFORM add_retention_policy('candles', INTERVAL '365 days');
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
  END IF;

  -- Keep execution telemetry longer for audit
  IF to_regclass('public.execution_events') IS NOT NULL THEN
    BEGIN
      PERFORM add_retention_policy('execution_events', INTERVAL '180 days');
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
  END IF;
  IF to_regclass('public.execution_logs') IS NOT NULL THEN
    BEGIN
      PERFORM add_retention_policy('execution_logs', INTERVAL '180 days');
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
  END IF;

  -- Scanner/signals history
  IF to_regclass('public.trading_signals') IS NOT NULL THEN
    BEGIN
      PERFORM add_retention_policy('trading_signals', INTERVAL '365 days');
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
  END IF;

  -- Position snapshots are short-lived
  IF to_regclass('public.mt5_position_snapshots') IS NOT NULL THEN
    BEGIN
      PERFORM add_retention_policy('mt5_position_snapshots', INTERVAL '30 days');
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
  END IF;

  -- Predictive reports can be kept long
  IF to_regclass('public.predictive_reports') IS NOT NULL THEN
    BEGIN
      PERFORM add_retention_policy('predictive_reports', INTERVAL '730 days');
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
  END IF;
END $$;