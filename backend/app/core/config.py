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
    # ? ????? asyncpg ??? ?????? ??????
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/revolution_x"
    # ? redis container ?????? ???? redis ???? docker-compose
    REDIS_URL: str = "redis://redis:6379/0"

    # -----------------------------
    # Security
    # -----------------------------
    SECRET_KEY: str = "your-secret-key-change-in-production"
    SECRET_SALT: str = "your-secret-salt-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # -----------------------------
    # CORS
    # -----------------------------
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://localhost:5173",
        # ? server ip
        "http://142.93.95.110:3000",
        "https://142.93.95.110:3000",
        "http://142.93.95.110",
        "https://142.93.95.110",
    ]

    # -----------------------------
    # MT5 (?? config.py ??????)
    # -----------------------------
    MT5_HOST: str = "localhost"
    MT5_PORT: int = 9000

    # -----------------------------
    # Telegram
    # -----------------------------
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # -----------------------------
    # Trading
    # -----------------------------
    TRADING_MODE: str = "paper"  # paper | live
    AUTO_START: bool = False

    # -----------------------------
    # AI Guardian
    # -----------------------------
    GUARDIAN_ENABLED: bool = True
    GUARDIAN_MODE: str = "semi_auto"  # auto | semi_auto | suggest_only
    GUARDIAN_LLM_PROVIDER: str = "gpt4"  # gpt4 | claude
    GUARDIAN_AUTO_FIX: bool = True
    GUARDIAN_APPROVAL_REQUIRED: bool = True
    GUARDIAN_LLM_ENABLED: bool = True

    # -----------------------------
    # API Keys
    # -----------------------------
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # -----------------------------
    # Pydantic v2 Config
    # -----------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()