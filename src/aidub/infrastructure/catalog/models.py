"""Typed values for the separate application project catalog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CatalogProject:
    project_id: str
    name: str
    path: Path
    last_opened_at: datetime
    pinned: bool
    created_at: datetime
    updated_at: datetime


class CatalogPathState(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    NOT_DIRECTORY = "NOT_DIRECTORY"
    UNSAFE = "UNSAFE"
    INVALID_SUFFIX = "INVALID_SUFFIX"


@dataclass(frozen=True, slots=True)
class CatalogPathInspection:
    path: Path
    state: CatalogPathState
    detail: str | None = None

    @property
    def available(self) -> bool:
        return self.state is CatalogPathState.AVAILABLE
