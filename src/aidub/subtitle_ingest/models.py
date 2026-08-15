"""Immutable, provider-neutral source subtitle ingestion contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from aidub.domain import (
    MediaAssetId,
    ProjectId,
    RationalRate,
    RationalTime,
    RoundingMode,
    TimeRange,
    Utterance,
    UtteranceStatus,
)
from aidub.domain.base import DomainModel
from aidub.domain.types import LanguageTag, LongText, NonEmptyStr, Sha256
from aidub.subtitles import SUBTITLE_RATE, SubtitleFormat


class SubtitleSourceEncoding(StrEnum):
    """The only encodings accepted at this untrusted-file boundary."""

    UTF8 = "utf-8"
    UTF8_BOM = "utf-8-bom"


class SubtitleTimingConflictSeverity(StrEnum):
    """Whether a detected timing condition permits candidate use."""

    WARNING = "warning"
    ERROR = "error"


class SubtitleTimingConflictCode(StrEnum):
    """Stable machine-readable timing conditions for UI and QC consumers."""

    OVERLAPPING_SOURCE_CUES = "overlapping_source_cues"
    OUTSIDE_MEDIA_DURATION = "outside_media_duration"
    EDIT_TIME_NOT_EXACT = "edit_time_not_exact"
    EDIT_RANGE_COLLAPSED = "edit_range_collapsed"


class SourceSubtitleProvenance(DomainModel):
    """Content identity retained without storing a machine-specific source path."""

    display_name: NonEmptyStr
    format: SubtitleFormat
    encoding: SubtitleSourceEncoding
    content_sha256: Sha256
    byte_length: int = Field(ge=0)
    language: LanguageTag


class SubtitleIngestionRequest(DomainModel):
    """Typed scope and exact-time policy for one source-subtitle import."""

    project_id: ProjectId
    media_asset_id: MediaAssetId
    source_language: LanguageTag
    media_duration: RationalTime | None = None
    edit_rate: RationalRate = SUBTITLE_RATE
    edit_rounding: RoundingMode | None = None
    maximum_bytes: int = Field(default=32 * 1024 * 1024, ge=1, le=512 * 1024 * 1024)
    maximum_cues: int = Field(default=100_000, ge=1, le=1_000_000)
    maximum_text_characters: int = Field(default=8_000_000, ge=1, le=64_000_000)

    @model_validator(mode="after")
    def _validate_policy(self) -> Self:
        if self.media_duration is not None and self.media_duration.ticks < 0:
            raise ValueError("media duration cannot be negative")
        return self


class SubtitleTimingConflict(DomainModel):
    """One deterministic, structured condition requiring caller acknowledgement."""

    code: SubtitleTimingConflictCode
    severity: SubtitleTimingConflictSeverity
    cue_number: int = Field(ge=1)
    source_range: TimeRange
    related_cue_number: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _validate_shape(self) -> Self:
        if self.source_range.rate != SUBTITLE_RATE:
            raise ValueError("source subtitle conflicts must use the 1000 Hz subtitle clock")
        if self.code is SubtitleTimingConflictCode.OVERLAPPING_SOURCE_CUES:
            if self.severity is not SubtitleTimingConflictSeverity.WARNING:
                raise ValueError("overlapping source cues are warnings")
            if self.related_cue_number is None:
                raise ValueError("overlap conflicts require a related cue number")
        elif self.related_cue_number is not None:
            raise ValueError("only overlap conflicts may name a related cue")
        if self.code is not SubtitleTimingConflictCode.OVERLAPPING_SOURCE_CUES:
            if self.severity is not SubtitleTimingConflictSeverity.ERROR:
                raise ValueError("non-overlap timing conflicts are blocking errors")
        return self


class SubtitleUtteranceCandidate(DomainModel):
    """A source-caption cue represented as a draft transcript candidate."""

    cue_number: int = Field(ge=1)
    cue_identifier: str | None = Field(default=None, min_length=1, max_length=512)
    cue_settings: str = Field(default="", max_length=2_048)
    source_range: TimeRange
    source_text: LongText
    source_text_sha256: Sha256
    utterance: Utterance

    @model_validator(mode="after")
    def _validate_candidate(self) -> Self:
        if self.source_range.rate != SUBTITLE_RATE:
            raise ValueError("source subtitle candidates must use the 1000 Hz subtitle clock")
        if self.source_range.is_empty:
            raise ValueError("source subtitle candidates must have positive duration")
        if self.utterance.source_range != self.source_range:
            raise ValueError("candidate source range must match its utterance")
        if self.utterance.source_text != self.source_text:
            raise ValueError("candidate source text must match its utterance")
        if self.utterance.status is not UtteranceStatus.DRAFT:
            raise ValueError("imported subtitle candidates must remain draft")
        if self.utterance.confidence != 0.0:
            raise ValueError("source subtitles do not carry ASR confidence")
        if "\x00" in self.cue_settings:
            raise ValueError("cue settings cannot contain NUL characters")
        return self


class SubtitleIngestionReport(DomainModel):
    """A complete, immutable report emitted for every successfully parsed source."""

    provenance: SourceSubtitleProvenance
    candidate_count: int = Field(ge=0)
    conflicts: tuple[SubtitleTimingConflict, ...] = ()

    @model_validator(mode="after")
    def _validate_conflict_order(self) -> Self:
        order = tuple(
            (
                conflict.cue_number,
                conflict.related_cue_number or 0,
                conflict.code.value,
            )
            for conflict in self.conflicts
        )
        if order != tuple(sorted(order)):
            raise ValueError("subtitle timing conflicts must have deterministic cue order")
        return self

    @property
    def blocking_conflicts(self) -> tuple[SubtitleTimingConflict, ...]:
        """Return conflicts that make the complete candidate set unsafe to consume."""

        return tuple(
            conflict
            for conflict in self.conflicts
            if conflict.severity is SubtitleTimingConflictSeverity.ERROR
        )

    @property
    def is_acceptable(self) -> bool:
        """Whether the candidate set has no unresolved blocking timing conditions."""

        return not self.blocking_conflicts


class SubtitleIngestionResult(DomainModel):
    """All-or-nothing candidate output plus its explicit timing report."""

    report: SubtitleIngestionReport
    candidates: tuple[SubtitleUtteranceCandidate, ...] = ()

    @model_validator(mode="after")
    def _validate_result(self) -> Self:
        if self.report.is_acceptable:
            if self.report.candidate_count != len(self.candidates):
                raise ValueError("acceptable reports must count every emitted candidate")
        elif self.candidates:
            raise ValueError("blocking timing conflicts require an empty candidate set")
        elif self.report.candidate_count != 0:
            raise ValueError("blocked reports cannot claim usable candidates")

        cue_numbers = tuple(candidate.cue_number for candidate in self.candidates)
        if cue_numbers != tuple(sorted(cue_numbers)):
            raise ValueError("subtitle candidates must be ordered by source cue number")
        utterance_ids = tuple(candidate.utterance.utterance_id for candidate in self.candidates)
        if len(utterance_ids) != len(set(utterance_ids)):
            raise ValueError("subtitle candidates must have unique utterance identifiers")
        return self


__all__ = [
    "SourceSubtitleProvenance",
    "SubtitleIngestionReport",
    "SubtitleIngestionRequest",
    "SubtitleIngestionResult",
    "SubtitleSourceEncoding",
    "SubtitleTimingConflict",
    "SubtitleTimingConflictCode",
    "SubtitleTimingConflictSeverity",
    "SubtitleUtteranceCandidate",
]
