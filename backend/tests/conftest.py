"""
Revolution X - Test Configuration
pytest fixtures and configuration
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.trading import Trade, Position
from app.core.security import create_access_token

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden dependencies."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@revolutionx.com",
        username="testuser",
        hashed_password="$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        is_active=True,
        is_superuser=False,
        trading_enabled=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_superuser(db_session: Session) -> User:
    """Create a test superuser."""
    user = User(
        email="admin@revolutionx.com",
        username="admin",
        hashed_password="$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        is_active=True,
        is_superuser=True,
        trading_enabled=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate authentication headers for test user."""
    access_token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_headers(test_superuser: User) -> dict:
    """Generate authentication headers for admin user."""
    access_token = create_access_token(subject=test_superuser.id)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "symbol": "EURUSD",
        "side": "buy",
        "entry_price": 1.0850,
        "exit_price": 1.0900,
        "quantity": 1.0,
        "stop_loss": 1.0800,
        "take_profit": 1.0950,
        "strategy": "SMC",
        "timeframe": "H1"
    }

@pytest.fixture
def mock_market_data():
    """Mock OHLCV market data."""
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range(start="2024-01-01", periods=100, freq="H")
    data = {
        'open': np.random.randn(100).cumsum() + 1.08,
        'high': np.random.randn(100).cumsum() + 1.085,
        'low': np.random.randn(100).cumsum() + 1.075,
        'close': np.random.randn(100).cumsum() + 1.08,
        'volume': np.random.randint(1000, 10000, 100)
    }
    return pd.DataFrame(data, index=dates)
