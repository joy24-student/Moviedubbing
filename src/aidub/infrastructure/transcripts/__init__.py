"""Durable transcript aggregate persistence."""

from .errors import (
    StoredTranscriptNotFoundError,
    StoredTranscriptRevisionConflict,
    TranscriptAlreadyExistsError,
    TranscriptPersistenceInvariantError,
    TranscriptStoreError,
)
from .repository import PersistedTranscriptMutation, TranscriptStore

__all__ = [
    "PersistedTranscriptMutation",
    "StoredTranscriptNotFoundError",
    "StoredTranscriptRevisionConflict",
    "TranscriptAlreadyExistsError",
    "TranscriptPersistenceInvariantError",
    "TranscriptStore",
    "TranscriptStoreError",
]
