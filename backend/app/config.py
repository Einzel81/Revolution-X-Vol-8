# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Revolution X"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/revolution_x"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://frontend:3000"]
    
    # MT5
    MT5_HOST: str = "localhost"
    MT5_PORT: int = 9000
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
