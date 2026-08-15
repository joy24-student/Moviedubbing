"""Project-lock failure hierarchy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import LockRecord


class ProjectLockError(RuntimeError):
    """Base class for project locking failures."""


class UnsafeLockPathError(ProjectLockError):
    """Raised when a lock path is not a regular managed file/directory."""


class LockContendedError(ProjectLockError):
    """Raised when another process or object holds the advisory lock."""

    def __init__(self, message: str, *, record: LockRecord | None = None) -> None:
        self.record = record
        super().__init__(message)


class OrphanedLockRecordError(ProjectLockError):
    """Raised when the OS lock is free but a prior owner's record remains."""

    def __init__(self, record: LockRecord) -> None:
        self.record = record
        super().__init__(
            "an orphaned project-lock record requires an explicit, audited break "
            f"using nonce {record.nonce}"
        )


class InvalidLockRecordError(ProjectLockError):
    """Raised when a lock record is malformed, oversized, or unsafe to read."""


class LockNonceMismatchError(ProjectLockError):
    """Raised when guarded break/release ownership does not match the record."""


class ActiveLockCannotBeBrokenError(ProjectLockError):
    """Raised when an explicit break is attempted while the OS lock is held."""


class LockRecordNotFoundError(ProjectLockError):
    """Raised when a guarded break finds no record to compare."""
