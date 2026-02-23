"""
Create initial admin user if not exists
Run inside container:

docker compose exec api python -m app.scripts.create_admin
"""

import asyncio
import os
from sqlalchemy import select

from app.database.connection import AsyncSessionLocal
from app.models.user import User
from app.core.security import security_manager


# ????? ????? ??? ????? ?? ??????? ??? environment variables
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin2@revolutionx.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")


async def create_admin():
    async with AsyncSessionLocal() as session:
        # ???? ?? ???????? ?????
        result = await session.execute(
            select(User).where(User.email == ADMIN_EMAIL)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"[OK] Admin already exists: {ADMIN_EMAIL}")
            return

        # ????? hash ????? ??????
        hashed_password = security_manager.hash_password(ADMIN_PASSWORD)

        # ????? ????????
        admin_user = User(
            email=ADMIN_EMAIL,
            password_hash=hashed_password,
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
        )

        session.add(admin_user)
        await session.commit()

        print("========================================")
        print("[CREATED] Admin user successfully created")
        print(f"Email: {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
        print("========================================")


if __name__ == "__main__":
    asyncio.run(create_admin())