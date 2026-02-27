from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.SETTINGS_ENCRYPTION_KEY.encode("utf-8")
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    f = _get_fernet()
    return f.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    f = _get_fernet()
    try:
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # If key changed or old data
        return ""