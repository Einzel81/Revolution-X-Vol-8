"""
Application Configuration
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    # -----------------------------
    # Core
    # -----------------------------
    APP_NAME: str = "Revolution X"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -----------------------------
    # Monitoring
    # -----------------------------
    SENTRY_DSN: Optional[str] = None

    # -----------------------------
    # Database
    # -----------------------------
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/revolution_x"
    REDIS_URL: str = "redis://redis:6379/0"

    # -----------------------------
    # Security
    # -----------------------------
    SECRET_KEY: str = "your-secret-key-change-in-production"
    SECRET_SALT: str = "your-secret-salt-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # -----------------------------
    # CORS
    # -----------------------------
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]

    # -----------------------------
    # MT5 Bridge (defaults; can be overridden per-connection)
    # -----------------------------
    MT5_HOST: str = "127.0.0.1"
    MT5_PORT: int = 9000
    MT5_BRIDGE_TOKEN: str = ""

    # IMPORTANT (LIVE + DOCKER):
    # If connection uses localhost/127.0.0.1, and API runs in Docker,
    # translate host to this docker-host gateway (or leave empty to auto-use 172.17.0.1).
    MT5_DOCKER_HOST: str = ""
    MT5_RESOLVE_LOCALHOST_IN_DOCKER: bool = True

    # -----------------------------
    # Trading Mode
    # -----------------------------
    TRADING_MODE: str = "paper"  # paper|live
    EXECUTION_BRIDGE: str = "mt5_tcp_json"

    # -----------------------------
    # Telegram
    # -----------------------------
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # -----------------------------
    # SMTP
    # -----------------------------
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()