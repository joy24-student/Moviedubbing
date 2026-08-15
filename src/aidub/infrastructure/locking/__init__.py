"""Exclusive project-lock public API."""

from .errors import (
    ActiveLockCannotBeBrokenError,
    InvalidLockRecordError,
    LockContendedError,
    LockNonceMismatchError,
    LockRecordNotFoundError,
    OrphanedLockRecordError,
    ProjectLockError,
    UnsafeLockPathError,
)
from .models import LockBreakEvent, LockInspection, LockRecord, LockState
from .project_lock import BreakAuditCallback, ProjectLock

__all__ = [
    "ActiveLockCannotBeBrokenError",
    "BreakAuditCallback",
    "InvalidLockRecordError",
    "LockBreakEvent",
    "LockContendedError",
    "LockInspection",
    "LockNonceMismatchError",
    "LockRecord",
    "LockRecordNotFoundError",
    "LockState",
    "OrphanedLockRecordError",
    "ProjectLock",
    "ProjectLockError",
    "UnsafeLockPathError",
]
