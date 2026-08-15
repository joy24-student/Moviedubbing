"""Failures raised by durable transcript storage."""

from __future__ import annotations


class TranscriptStoreError(RuntimeError):
    """Base error for transcript persistence failures."""


class TranscriptAlreadyExistsError(TranscriptStoreError):
    """Raised when an initial transcript snapshot already exists."""


class StoredTranscriptNotFoundError(TranscriptStoreError):
    """Raised when a requested transcript snapshot is absent."""


class StoredTranscriptRevisionConflict(TranscriptStoreError):
    """Raised when a mutation was prepared against a stale durable revision."""


class TranscriptPersistenceInvariantError(TranscriptStoreError):
    """Raised when a mutation result cannot be safely committed."""


__all__ = [
    "StoredTranscriptNotFoundError",
    "StoredTranscriptRevisionConflict",
    "TranscriptAlreadyExistsError",
    "TranscriptPersistenceInvariantError",
    "TranscriptStoreError",
]
