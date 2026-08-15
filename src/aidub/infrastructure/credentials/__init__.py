"""Secret storage adapters."""

from .base import MemorySecretStore, SecretStore
from .dpapi import DpapiFileSecretStore, DpapiUnavailableError

__all__ = [
    "DpapiFileSecretStore",
    "DpapiUnavailableError",
    "MemorySecretStore",
    "SecretStore",
]
