import pytest
from typing import AsyncGenerator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.database.connection import Base
from app.database.connection import get_db as real_get_db
from app.auth.dependencies import require_trader

import app.models  # noqa: F401


class FakeUser:
    def __init__(self):
        self.id = "00000000-0000-0000-0000-000000000001"
        self.role = "trader"


@pytest.fixture(scope="session")
def test_db_url() -> str:
    # Use TEST_DATABASE_URL if present; fallback to DATABASE_URL
    return getattr(settings, "TEST_DATABASE_URL", None) or settings.DATABASE_URL


@pytest.fixture(scope="function")
async def db_session(test_db_url: str) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(test_db_url, echo=False, future=True)
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    async def override_require_trader():
        return FakeUser()

    app.dependency_overrides[real_get_db] = override_get_db
    app.dependency_overrides[require_trader] = override_require_trader

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()