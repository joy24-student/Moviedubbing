"""Per-language localization state and versioned translation decisions."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel, UtcDatetime, utc_now
from .identifiers import (
    LocalizationId,
    ProjectId,
    TranslationVersionId,
    UtteranceId,
    VoiceProfileId,
)
from .types import LanguageTag, LongText, NonEmptyStr, Sha256, require_unique


class LocalizationStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    RENDERED = "rendered"
    STALE = "stale"
    ARCHIVED = "archived"


class TranslationOrigin(StrEnum):
    HUMAN = "human"
    PROVIDER = "provider"
    LOCAL_MODEL = "local_model"
    IMPORT = "import"


class TranslationStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    STALE = "stale"
    REJECTED = "rejected"


class Localization(DomainModel):
    """Independent target-language branch over shared source analysis."""

    localization_id: LocalizationId
    project_id: ProjectId
    source_language: LanguageTag
    target_language: LanguageTag
    display_name: NonEmptyStr
    status: LocalizationStatus = LocalizationStatus.PLANNED
    default_voice_profile_ids: tuple[VoiceProfileId, ...] = ()
    glossary_version: int = Field(default=0, ge=0)
    translation_memory_version: int = Field(default=0, ge=0)
    revision: int = Field(default=0, ge=0)
    created_at: UtcDatetime = Field(default_factory=utc_now)
    updated_at: UtcDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _validate_localization(self) -> Self:
        if self.source_language.casefold() == self.target_language.casefold():
            raise ValueError("localization target must differ from its source language")
        require_unique(
            self.default_voice_profile_ids,
            field_name="default_voice_profile_ids",
        )
        if self.updated_at < self.created_at:
            raise ValueError("localization update timestamp cannot precede creation")
        return self


class TranslationWarning(DomainModel):
    code: NonEmptyStr
    message: NonEmptyStr
    blocking: bool = False


class TranslationVersion(DomainModel):
    """Immutable translation revision with human/provider provenance."""

    translation_version_id: TranslationVersionId
    utterance_id: UtteranceId
    localization_id: LocalizationId
    version: int = Field(ge=1)
    source_utterance_sha256: Sha256
    target_text: LongText
    origin: TranslationOrigin
    status: TranslationStatus = TranslationStatus.DRAFT
    provider_id: NonEmptyStr | None = None
    model_id: NonEmptyStr | None = None
    prompt_version: NonEmptyStr | None = None
    glossary_version: int = Field(default=0, ge=0)
    estimated_duration_ms: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    warnings: tuple[TranslationWarning, ...] = ()
    created_by: NonEmptyStr
    created_at: UtcDatetime = Field(default_factory=utc_now)
    approved_by: NonEmptyStr | None = None
    approved_at: UtcDatetime | None = None

    @model_validator(mode="after")
    def _validate_provenance(self) -> Self:
        if self.origin is TranslationOrigin.PROVIDER and (
            self.provider_id is None or self.model_id is None or self.prompt_version is None
        ):
            raise ValueError("provider translation requires provider, model, and prompt versions")
        if self.origin is TranslationOrigin.LOCAL_MODEL and self.model_id is None:
            raise ValueError("local-model translation requires a model identifier")
        if self.status is TranslationStatus.APPROVED:
            if self.approved_by is None or self.approved_at is None:
                raise ValueError("approved translation requires approver and timestamp")
            if self.approved_at < self.created_at:
                raise ValueError("translation cannot be approved before creation")
        elif self.approved_by is not None or self.approved_at is not None:
            raise ValueError("only approved translations may carry approval details")
        return self


__all__ = [
    "Localization",
    "LocalizationStatus",
    "TranslationOrigin",
    "TranslationStatus",
    "TranslationVersion",
    "TranslationWarning",
]
