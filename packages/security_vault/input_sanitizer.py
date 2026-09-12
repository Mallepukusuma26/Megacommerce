"""
MegaCommerce Security Vault — Input Sanitization & Threat Prevention
"""

import re
import html
from typing import Any, Dict, List


class InputSanitizer:
    """Sanitizes user input to prevent XSS, SQLi, and script injection attacks."""

    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION)\b)", re.IGNORECASE),
        re.compile(r"(--|\/\*|\*\/|;)", re.IGNORECASE)
    ]

    SCRIPT_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"onload\s*=", re.IGNORECASE),
        re.compile(r"onerror\s*=", re.IGNORECASE)
    ]

    @classmethod
    def sanitize_string(cls, text: str) -> str:
        if not text:
            return ""

        # Remove script tags and inline handlers
        for pattern in cls.SCRIPT_PATTERNS:
            text = pattern.sub("", text)

        # HTML escape
        escaped = html.escape(text.strip())
        return escaped

    @classmethod
    def contains_sqli_threat(cls, text: str) -> bool:
        if not text:
            return False
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, val in data.items():
            if isinstance(val, str):
                sanitized[key] = cls.sanitize_string(val)
            elif isinstance(val, dict):
                sanitized[key] = cls.sanitize_dict(val)
            elif isinstance(val, list):
                sanitized[key] = [cls.sanitize_string(item) if isinstance(item, str) else item for item in val]
            else:
                sanitized[key] = val
        return sanitized
