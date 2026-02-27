"""
Revolution X - Security Core
Authentication, authorization, and encryption
"""
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.core.config import settings
from app.core.logging import get_logger, audit_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


class SecurityManager:
    """Centralized security management."""

    def __init__(self):
        self._encryption_key = self._derive_key(settings.SECRET_KEY)
        self._fernet = Fernet(self._encryption_key)

    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=settings.SECRET_SALT.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash.

        IMPORTANT:
        - Never raise on malformed/unknown hashes; return False instead.
        - This prevents /auth/login from returning 500 when DB contains an invalid hash.
        """
        try:
            if not hashed_password:
                return False
            return pwd_context.verify(plain_password, hashed_password)
        except UnknownHashError:
            # DB contains a hash which passlib cannot identify (corrupted / unsupported scheme)
            logger.warning("Unknown password hash format encountered during login.")
            return False
        except Exception as e:
            # Any other backend error should not crash authentication
            logger.exception(f"Password verify error: {e}")
            return False

    def create_access_token(
        self,
        subject: Union[str, int],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[dict] = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": secrets.token_urlsafe(16)  # Unique token ID for revocation
        }

        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    def create_refresh_token(self, subject: Union[str, int]) -> str:
        """Create JWT refresh token."""
        days = int(getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30))
        expire = datetime.utcnow() + timedelta(days=days)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16)
        }

        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token decode error: {e}")
            return None

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data."""
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None

    def generate_api_key(self) -> str:
        """Generate secure API key."""
        return f"rx_{secrets.token_urlsafe(32)}"

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)

    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash."""
        return hmac.compare_digest(
            self.hash_api_key(api_key),
            hashed_key
        )

    def generate_csrf_token(self) -> str:
        """Generate CSRF protection token."""
        return secrets.token_urlsafe(32)

    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input."""
        import html

        # Remove null bytes
        sanitized = input_str.replace('\x00', '')

        # HTML escape
        sanitized = html.escape(sanitized)

        # Remove potential script tags
        sanitized = sanitized.replace('<script>', '').replace('</script>', '')

        return sanitized

    def validate_password_strength(self, password: str) -> dict:
        """Validate password strength."""
        import re

        result = {
            "valid": True,
            "score": 0,
            "errors": []
        }

        # Length check
        if len(password) < 8:
            result["errors"].append("Password must be at least 8 characters")
            result["valid"] = False
        else:
            result["score"] += 1

        # Uppercase check
        if not re.search(r'[A-Z]', password):
            result["errors"].append("Password must contain uppercase letter")
            result["valid"] = False
        else:
            result["score"] += 1

        # Lowercase check
        if not re.search(r'[a-z]', password):
            result["errors"].append("Password must contain lowercase letter")
            result["valid"] = False
        else:
            result["score"] += 1

        # Digit check
        if not re.search(r'\d', password):
            result["errors"].append("Password must contain digit")
            result["valid"] = False
        else:
            result["score"] += 1

        # Special character check
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result["errors"].append("Password must contain special character")
            result["valid"] = False
        else:
            result["score"] += 1

        return result


class TokenBlacklist:
    """Token blacklist for logout functionality."""

    def __init__(self):
        self._blacklist = set()
        self._last_cleanup = datetime.utcnow()

    def blacklist_token(self, jti: str, exp: datetime):
        """Add token to blacklist."""
        self._blacklist.add((jti, exp))
        self._cleanup()

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        return any(token_id == jti for token_id, _ in self._blacklist)

    def _cleanup(self):
        """Remove expired tokens from blacklist."""
        now = datetime.utcnow()
        if now - self._last_cleanup > timedelta(hours=1):
            self._blacklist = {
                (jti, exp) for jti, exp in self._blacklist
                if exp > now
            }
            self._last_cleanup = now


# Global instances
security_manager = SecurityManager()
token_blacklist = TokenBlacklist()


# Password policies
PASSWORD_POLICIES = {
    "min_length": 8,
    "max_length": 128,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digits": True,
    "require_special": True,
    "prevent_common": True,
    "max_age_days": 90,
    "history_count": 5
}

# Common passwords to block
COMMON_PASSWORDS = {
    'password', '123456', '12345678', 'qwerty', 'abc123',
    'monkey', 'letmein', 'dragon', '111111', 'baseball'
}


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)