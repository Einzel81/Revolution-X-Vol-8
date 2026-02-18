"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Revolution X"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/revolution_x"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Trading
    TRADING_MODE: str = "paper"  # paper, live
    AUTO_START: bool = False
    
    # AI Guardian
    GUARDIAN_ENABLED: bool = True
    GUARDIAN_MODE: str = "semi_auto"  # auto, semi_auto, suggest_only
    GUARDIAN_LLM_PROVIDER: str = "gpt4"  # gpt4, claude
    GUARDIAN_AUTO_FIX: bool = True
    GUARDIAN_APPROVAL_REQUIRED: bool = True
    GUARDIAN_LLM_ENABLED: bool = True
    
    # API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
