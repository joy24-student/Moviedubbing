"""Rejected transcript editing operations."""

from __future__ import annotations

from aidub.domain.base import DomainError


class TranscriptError(DomainError):
    """Base class for a rejected transcript operation."""


class TranscriptRevisionConflict(TranscriptError):
    """The command was based on a transcript revision that is no longer current."""

    def __init__(self, *, expected: int, current: int) -> None:
        self.expected = expected
        self.current = current
        super().__init__(f"expected transcript revision {expected}, current revision is {current}")


class UtteranceNotFound(TranscriptError):
    """The requested utterance is not part of the transcript snapshot."""


class LockedFieldViolation(TranscriptError):
    """A command attempted to modify a protected utterance field."""


class TranscriptInvariantViolation(TranscriptError):
    """A command would create an invalid transcript snapshot."""


__all__ = [
    "LockedFieldViolation",
    "TranscriptError",
    "TranscriptInvariantViolation",
    "TranscriptRevisionConflict",
    "UtteranceNotFound",
]
