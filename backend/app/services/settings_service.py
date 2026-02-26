from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.app_setting import AppSetting
from app.utils.crypto import encrypt_secret, decrypt_secret


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str, *, decrypt: bool = True) -> Optional[str]:
        row = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        setting = row.scalar_one_or_none()
        if not setting:
            return None
        if setting.is_secret and decrypt and setting.value:
            return decrypt_secret(setting.value)
        return setting.value

    async def set(self, key: str, value: Optional[str], *, is_secret: bool = False) -> None:
        row = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        setting = row.scalar_one_or_none()

        stored_value = value
        if is_secret and value:
            stored_value = encrypt_secret(value)

        if not setting:
            setting = AppSetting(
                key=key,
                value=stored_value,
                is_secret=is_secret,
                updated_at=datetime.utcnow(),
            )
            self.db.add(setting)
        else:
            setting.value = stored_value
            setting.is_secret = is_secret
            setting.updated_at = datetime.utcnow()

        await self.db.commit()

    async def get_public_settings(self) -> Dict[str, Any]:
        """
        Returns only non-secret keys; for secret keys we return is_set boolean.
        """
        rows = await self.db.execute(select(AppSetting))
        settings_rows = rows.scalars().all()

        out: Dict[str, Any] = {}
        for s in settings_rows:
            if s.is_secret:
                out[s.key] = {"is_secret": True, "is_set": bool(s.value)}
            else:
                out[s.key] = {"is_secret": False, "value": s.value}
        return out