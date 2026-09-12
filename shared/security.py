"""
MegaCommerce Security, Token Management, & Cryptographic Utilities
Zero External API Key Compliance Architecture
"""

import datetime
from typing import Optional, Dict, Any, List
import jwt
from passlib.context import CryptContext
from config.settings import settings
from shared.enums import UserRole
from shared.exceptions import AuthenticationError, AuthorizationError


# Cryptographic Context using Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hashes a plain-text password using bcrypt algorithm."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed bcrypt password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    email: str,
    role: UserRole,
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Generates a signed JWT access token for authenticated users."""
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email,
        "role": role.value if isinstance(role, UserRole) else str(role),
        "iat": now,
        "exp": expire,
        "iss": "MegaCommerce-Security-Engine"
    }

    token = jwt.encode(
        payload,
        settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM
    )
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a signed JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.security.SECRET_KEY,
            algorithms=[settings.security.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("JWT token has expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid authentication token: {str(e)}")


def verify_user_role(token_payload: Dict[str, Any], allowed_roles: List[UserRole]) -> bool:
    """Checks if token role matches required allowed roles."""
    user_role_str = token_payload.get("role")
    allowed_str_list = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]
    if user_role_str not in allowed_str_list:
        raise AuthorizationError(
            f"Access denied for role '{user_role_str}'. Required roles: {allowed_str_list}"
        )
    return True
