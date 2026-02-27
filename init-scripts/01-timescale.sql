-- init-scripts/01-timescale.sql
-- Runs once on first database initialization (POSTGRES_DB=revolution_x)

-- TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Optional but useful extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Hypertables are created after SQLAlchemy creates the tables
-- (see backend/app/database/connection.py)
