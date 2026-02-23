# backend/app/models/user.py

import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

from app.database.connection import Base  # ????? Base

# ?????? ENUM ??????? ?? PostgreSQL ???? ????? ????? ????
UserRoleEnum = ENUM(name="userrole", create_type=False)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # ? ??? ?????? ??????? ?? DB
    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(255), nullable=False)

    role = Column(UserRoleEnum, nullable=False)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ?? metadata ??? ????? ?? SQLAlchemy ? ????? ???? ??? ?? ??????
    metadata_json = Column("metadata", JSONB, nullable=True)