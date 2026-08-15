"""Credential store abstraction."""

from __future__ import annotations

from typing import Protocol


class SecretStore(Protocol):
    def set(self, name: str, value: str) -> None: ...

    def get(self, name: str) -> str | None: ...

    def delete(self, name: str) -> bool: ...


class MemorySecretStore:
    """Non-persistent store for tests and explicitly ephemeral sessions."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def set(self, name: str, value: str) -> None:
        if not name or not value:
            raise ValueError("secret name and value must not be empty")
        self._values[name] = value

    def get(self, name: str) -> str | None:
        return self._values.get(name)

    def delete(self, name: str) -> bool:
        return self._values.pop(name, None) is not None
