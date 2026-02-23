# backend/app/auth/models.py
"""
Compatibility layer:
- Avoid defining ORM tables here (prevents duplicate 'users' table mapping).
- Re-export canonical User model.
- Provide UserRole enum used by dependencies/router.
"""

from enum import Enum
from app.models.user import User  # canonical ORM model


class UserRole(str, Enum):
    # These should match the Postgres enum `userrole` values.
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    TRADER = "TRADER"
    USER = "USER"
    VIEWER = "VIEWER"


__all__ = ["User", "UserRole"]