"""Strict commands accepted by the local-first translation workflow."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from aidub.domain import TranslationOrigin, TranslationVersionId, TranslationWarning, UtteranceId
from aidub.domain.base import DomainModel, UtcDatetime, utc_now
from aidub.domain.types import LongText, NonEmptyStr, Sha256

from .models import TranslationProviderResult


class TranslationCommand(DomainModel):
    """Compare-and-swap command metadata shared by every mutation."""

    expected_revision: int = Field(ge=0)
    actor: NonEmptyStr
    occurred_at: UtcDatetime = Field(default_factory=utc_now)


class SyncSourceCommand(TranslationCommand):
    """Record the current source text revision without retaining its text content."""

    utterance_id: UtteranceId
    source_text_sha256: Sha256
    source_revision: int = Field(ge=0)


class CreateTranslationDraftCommand(TranslationCommand):
    """Create a human, import, or local-model translation draft.

    Raw provider output is deliberately rejected here; it must first pass through
    ``ProviderTranslationResultValidator`` and then use the dedicated command.
    """

    translation_version_id: TranslationVersionId
    utterance_id: UtteranceId
    source_text_sha256: Sha256
    source_revision: int = Field(ge=0)
    target_text: LongText
    origin: TranslationOrigin = TranslationOrigin.HUMAN
    model_id: NonEmptyStr | None = None
    estimated_duration_ms: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    warnings: tuple[TranslationWarning, ...] = ()

    @model_validator(mode="after")
    def _validate_origin(self) -> Self:
        if self.origin is TranslationOrigin.PROVIDER:
            raise ValueError("provider output must use ApplyProviderTranslationCommand")
        if self.origin is TranslationOrigin.LOCAL_MODEL and self.model_id is None:
            raise ValueError("local-model drafts require a model identifier")
        if self.origin is not TranslationOrigin.LOCAL_MODEL and self.model_id is not None:
            raise ValueError("only local-model drafts may carry a model identifier")
        return self


class ApplyProviderTranslationCommand(TranslationCommand):
    """Persist a provider result that has already passed the validation boundary."""

    translation_version_id: TranslationVersionId
    result: TranslationProviderResult


class SendTranslationToReviewCommand(TranslationCommand):
    """Turn a selected draft into a new immutable review revision."""

    translation_version_id: TranslationVersionId
    new_translation_version_id: TranslationVersionId


class ApproveTranslationCommand(TranslationCommand):
    """Turn a selected review revision into a new immutable approved revision."""

    translation_version_id: TranslationVersionId
    new_translation_version_id: TranslationVersionId


class RejectTranslationCommand(TranslationCommand):
    """Record a rejected draft/review revision and remove it from active selection."""

    translation_version_id: TranslationVersionId
    new_translation_version_id: TranslationVersionId


class UpdateTranslationResourcesCommand(TranslationCommand):
    """Advance glossary and/or translation-memory dependency versions monotonically."""

    glossary_version: int | None = Field(default=None, ge=0)
    translation_memory_version: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _require_change(self) -> Self:
        if self.glossary_version is None and self.translation_memory_version is None:
            raise ValueError("at least one translation resource version must be supplied")
        return self


__all__ = [
    "ApplyProviderTranslationCommand",
    "ApproveTranslationCommand",
    "CreateTranslationDraftCommand",
    "RejectTranslationCommand",
    "SendTranslationToReviewCommand",
    "SyncSourceCommand",
    "TranslationCommand",
    "UpdateTranslationResourcesCommand",
]
