"""Explicit failures for the source-subtitle ingestion boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SubtitleIngestionReport


class SubtitleIngestionError(ValueError):
    """Base error for a source subtitle that cannot safely enter the project."""


class UnsafeSubtitleSourceError(SubtitleIngestionError):
    """Raised when the selected source is not a regular, safe-to-read file."""


class UnsupportedSubtitleEncodingError(SubtitleIngestionError):
    """Raised when source bytes are not UTF-8 or UTF-8 with a BOM."""


class SubtitleIngestionConflictError(SubtitleIngestionError):
    """Raised only when a caller explicitly requires an acceptable report."""

    def __init__(self, report: SubtitleIngestionReport) -> None:
        self.report = report
        super().__init__(
            "source subtitle has blocking timing conflicts: "
            + ", ".join(conflict.code.value for conflict in report.blocking_conflicts)
        )


__all__ = [
    "SubtitleIngestionConflictError",
    "SubtitleIngestionError",
    "UnsafeSubtitleSourceError",
    "UnsupportedSubtitleEncodingError",
]
