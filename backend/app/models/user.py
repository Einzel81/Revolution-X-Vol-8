# backend/app/models/user.py

import datetime
import uuid
import enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum as SAEnum

from app.database.connection import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    trader = "trader"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String(255), unique=True, index=True, nullable=False)

    # password hash stored in DB
    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(255), nullable=False)

    # CHECK constraint instead of Postgres ENUM type (simpler in dev)
    role = Column(
        SAEnum(UserRole, name="userrole", create_constraint=True),
        nullable=False,
        default=UserRole.trader,
    )

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # keep DB column name "metadata"
    metadata_json = Column("metadata", JSONB, nullable=True)