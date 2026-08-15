"""Persistence-specific exception hierarchy.

The infrastructure layer deliberately exposes domain-neutral exceptions so that
callers do not need to depend on :mod:`sqlite3` details.
"""

from __future__ import annotations


class PersistenceError(RuntimeError):
    """Base class for project database failures."""


class DatabaseNotInitializedError(PersistenceError):
    """Raised when a project database has no migration history."""


class MigrationError(PersistenceError):
    """Raised when migrations cannot be discovered or applied safely."""


class MigrationIntegrityError(MigrationError):
    """Raised when an already-applied migration has changed on disk."""


class NewerSchemaError(MigrationError):
    """Raised when a writable open is attempted on a newer project schema."""

    def __init__(self, found_version: int, supported_version: int) -> None:
        self.found_version = found_version
        self.supported_version = supported_version
        super().__init__(
            f"project schema {found_version} is newer than supported schema "
            f"{supported_version}; open it read-only with a newer application"
        )


class IntegrityCheckError(PersistenceError):
    """Raised when SQLite reports database or foreign-key corruption."""


class InvalidStateTransitionError(PersistenceError):
    """Raised when a job state transition violates the state machine."""
