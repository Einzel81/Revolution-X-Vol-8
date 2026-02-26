from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    from app.models import user  # noqa: F401
    from app.models import trade  # noqa: F401
    from app.models import alert  # noqa: F401
    from app.models import notification  # noqa: F401
    from app.models import telegram_user  # noqa: F401
    from app.models import execution_event  # noqa: F401
    from app.models import mt5_position_snapshot  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session