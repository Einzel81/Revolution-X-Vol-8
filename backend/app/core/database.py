from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# إنشاء محرك قاعدة البيانات
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
)

# إنشاء SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# إنشاء Base
Base = declarative_base()

# دالة للحصول على DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
