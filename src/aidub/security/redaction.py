"""Deterministic redaction for logs and support bundles."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "cookie",
        "password",
        "refresh_token",
        "secret",
        "session",
        "token",
    }
)

_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-=]+")
_COMMON_KEY = re.compile(r"(?i)\b(?:sk|key|token)-[A-Za-z0-9_-]{8,}\b")


class Redactor:
    replacement = "[REDACTED]"

    @classmethod
    def text(cls, value: str) -> str:
        value = _BEARER.sub(f"Bearer {cls.replacement}", value)
        return _COMMON_KEY.sub(cls.replacement, value)

    @classmethod
    def value(cls, value: Any, *, key: str | None = None) -> Any:
        if key is not None and key.casefold() in _SECRET_KEYS:
            return cls.replacement
        if isinstance(value, str):
            return cls.text(value)
        if isinstance(value, Mapping):
            return {
                str(item_key): cls.value(item_value, key=str(item_key))
                for item_key, item_value in value.items()
            }
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [cls.value(item) for item in value]
        return value
