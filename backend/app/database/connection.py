# backend/app/database/connection.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# ? ????? ???? settings
from app.config import settings  # ??? ???? wrapper ??? app.core.config

# Base ???? ??? ???????
Base = declarative_base()

# Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=getattr(settings, "DEBUG", False),
    future=True,
)

# Async Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    # ????? ??????? ?? ?? ??? ?????? (???? ???????)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)