"""Project manifest and project-wide editorial settings."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel, UtcDatetime, utc_now
from .identifiers import LocalizationId, MediaAssetId, ProjectId
from .rights import SourceAuthorization
from .time import RationalRate
from .types import LanguageTag, NonEmptyStr, require_unique


class ProjectState(StrEnum):
    ACTIVE = "active"
    READ_ONLY = "read_only"
    DEGRADED = "degraded"
    RECOVERY = "recovery"
    ARCHIVED = "archived"


class PrivacyMode(StrEnum):
    OFFLINE = "offline"
    HYBRID = "hybrid"
    CLOUD_ASSISTED = "cloud_assisted"
    STUDIO_LOCKED = "studio_locked"


class QualityPreset(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    PROFESSIONAL = "professional"
    CINEMA = "cinema"


class ProjectSettings(DomainModel):
    """Settings whose values affect editorial math or reproducible generation."""

    video_rate: RationalRate
    audio_sample_rate: int = Field(default=48_000, ge=8_000, le=384_000)
    source_language: LanguageTag
    quality_preset: QualityPreset = QualityPreset.PROFESSIONAL
    privacy_mode: PrivacyMode = PrivacyMode.OFFLINE
    working_color_space: NonEmptyStr = "Rec.709 Gamma 2.4"
    allow_external_text: bool = False
    allow_external_media: bool = False

    @model_validator(mode="after")
    def _enforce_network_policy(self) -> Self:
        if self.privacy_mode is PrivacyMode.OFFLINE and (
            self.allow_external_text or self.allow_external_media
        ):
            raise ValueError("offline projects cannot permit external data disclosure")
        if self.allow_external_media and not self.allow_external_text:
            raise ValueError("external media permission implies external text permission")
        return self


class Project(DomainModel):
    """Versioned root aggregate persisted in a project package manifest."""

    project_id: ProjectId
    schema_version: int = Field(default=1, ge=1)
    name: NonEmptyStr
    state: ProjectState = ProjectState.ACTIVE
    settings: ProjectSettings
    source_authorization: SourceAuthorization
    primary_media_asset_id: MediaAssetId | None = None
    localization_ids: tuple[LocalizationId, ...] = ()
    revision: int = Field(default=0, ge=0)
    created_at: UtcDatetime = Field(default_factory=utc_now)
    updated_at: UtcDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _validate_project(self) -> Self:
        require_unique(self.localization_ids, field_name="localization_ids")
        if self.updated_at < self.created_at:
            raise ValueError("project update timestamp cannot precede creation")
        return self


__all__ = [
    "PrivacyMode",
    "Project",
    "ProjectSettings",
    "ProjectState",
    "QualityPreset",
]
