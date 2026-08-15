"""Rejected translation-workflow operations."""

from __future__ import annotations

from aidub.domain.base import DomainError


class TranslationError(DomainError):
    """Base class for translation workflow failures."""


class TranslationRevisionConflict(TranslationError):
    """A command was based on an aggregate revision that is no longer current."""

    def __init__(self, *, expected: int, current: int) -> None:
        self.expected = expected
        self.current = current
        super().__init__(
            f"expected translation aggregate revision {expected}, current revision is {current}"
        )


class TranslationUnitNotFound(TranslationError):
    """The requested source utterance is absent from a localization aggregate."""


class TranslationVersionNotFound(TranslationError):
    """The requested immutable translation revision is absent from a unit."""


class TranslationInvariantViolation(TranslationError):
    """A command would create an invalid translation aggregate."""


class TranslationStaleViolation(TranslationError):
    """A workflow transition requires a translation with current dependencies."""


class ProviderTranslationResultRejected(TranslationError):
    """An untrusted provider result did not match its validated request scope."""


__all__ = [
    "ProviderTranslationResultRejected",
    "TranslationError",
    "TranslationInvariantViolation",
    "TranslationRevisionConflict",
    "TranslationStaleViolation",
    "TranslationUnitNotFound",
    "TranslationVersionNotFound",
]
