"""
MegaCommerce Authentication & RBAC Middleware Helpers for Flask/REST API
"""

from functools import wraps
from typing import List, Callable, Optional
from flask import request, jsonify, g
from shared.security import decode_access_token, verify_user_role
from shared.enums import UserRole
from shared.exceptions import AuthenticationError, AuthorizationError


def get_token_from_header() -> str:
    """Extracts Bearer token from HTTP Authorization Header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError("Authorization header is missing.")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'.")

    return parts[1]


def require_auth(roles: Optional[List[UserRole]] = None) -> Callable:
    """Decorator for enforcing JWT authentication and role-based access control (RBAC)."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_from_header()
                payload = decode_access_token(token)
                
                # Check role permissions if specified
                if roles:
                    verify_user_role(payload, roles)

                # Attach user identity to Flask context
                g.current_user = {
                    "id": payload["sub"],
                    "email": payload["email"],
                    "role": payload["role"]
                }
            except (AuthenticationError, AuthorizationError) as err:
                return jsonify(err.to_dict()), err.status_code
            except Exception as e:
                return jsonify({"error": True, "code": "AUTH_ERROR", "message": str(e)}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorator
