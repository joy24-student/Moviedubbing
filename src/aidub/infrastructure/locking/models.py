"""Typed project-lock records, inspections, and break-audit events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LockRecord:
    process_id: int
    hostname: str
    started_at: str
    nonce: str
    format_version: int = 1


class LockState(StrEnum):
    UNLOCKED = "UNLOCKED"
    HELD = "HELD"
    ORPHANED = "ORPHANED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class LockInspection:
    state: LockState
    lock_path: Path
    record_path: Path
    record: LockRecord | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class LockBreakEvent:
    project_path: Path
    record: LockRecord
    broken_at: str
    breaker_process_id: int
    breaker_hostname: str
    reason: str
