"""Typed values returned by the immutable artifact store."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class StagedArtifact:
    token: str
    path: Path
    byte_length: int


@dataclass(frozen=True, slots=True)
class PublishedArtifact:
    sha256: str
    byte_length: int
    relative_path: str
    path: Path
    deduplicated: bool


class ValidationState(StrEnum):
    VALID = "VALID"
    MISSING = "MISSING"
    SIZE_MISMATCH = "SIZE_MISMATCH"
    HASH_MISMATCH = "HASH_MISMATCH"
    UNSAFE = "UNSAFE"
    NOT_REGULAR_FILE = "NOT_REGULAR_FILE"


@dataclass(frozen=True, slots=True)
class ArtifactValidation:
    sha256: str
    state: ValidationState
    path: Path
    expected_size: int | None = None
    actual_size: int | None = None
    actual_sha256: str | None = None
    detail: str | None = None

    @property
    def valid(self) -> bool:
        return self.state is ValidationState.VALID


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    valid_objects: tuple[str, ...]
    missing_objects: tuple[str, ...]
    corrupt_objects: tuple[str, ...]
    orphan_objects: tuple[str, ...]
    staged_removed: tuple[str, ...]
    staged_retained: tuple[str, ...]
    unsafe_entries: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not (
            self.missing_objects or self.corrupt_objects or self.unsafe_entries or self.errors
        )
