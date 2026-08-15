"""Strict, provider-neutral speech-recognition contracts.

Speech timing is represented exclusively in the source audio sample clock.  No
floating-point seconds cross this boundary, which makes long-form recognition
replayable and prevents cumulative timestamp drift.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import ConfigDict, Field, StringConstraints, model_validator

from aidub.contracts.base import ContractModel, Identifier
from aidub.domain.identifiers import MediaAssetId, ProjectId
from aidub.domain.time import AudioSampleRange
from aidub.domain.types import LanguageTag, SemanticVersion, Sha256

SpeechText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100_000),
]
WordText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1_024),
]


class SpeechContractModel(ContractModel):
    """Base for immutable speech contracts with coercion disabled."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_default=True,
    )


class SpeechEngineIdentity(SpeechContractModel):
    """Immutable identity of the executable and exact model weights used."""

    engine_id: Identifier
    engine_version: SemanticVersion
    model_id: Identifier
    model_version: SemanticVersion
    model_weights_sha256: Sha256


class SpeechRecognitionRequest(SpeechContractModel):
    """A request for one chunk of a potentially long source-audio range."""

    request_id: Identifier
    project_id: ProjectId
    media_asset_id: MediaAssetId
    source_audio_sha256: Sha256
    language: LanguageTag
    full_audio_range: AudioSampleRange
    audio_range: AudioSampleRange
    channel_index: int = Field(default=0, ge=0, le=255)
    chunk_index: int = Field(default=0, ge=0)
    chunk_count: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def _validate_request_range(self) -> Self:
        if self.full_audio_range.is_empty:
            raise ValueError("full audio range cannot be empty")
        if self.audio_range.is_empty:
            raise ValueError("recognition audio range cannot be empty")
        if self.full_audio_range.sample_rate != self.audio_range.sample_rate:
            raise ValueError("full and chunk audio ranges use different sample rates")
        full_start = self.full_audio_range.start.sample_index
        full_end = self.full_audio_range.end_exclusive.sample_index
        chunk_start = self.audio_range.start.sample_index
        chunk_end = self.audio_range.end_exclusive.sample_index
        if chunk_start < full_start or chunk_end > full_end:
            raise ValueError("recognition chunk must be contained in the full audio range")
        if self.chunk_index >= self.chunk_count:
            raise ValueError("chunk index must be less than chunk count")
        return self


class RecognitionProvenance(SpeechContractModel):
    """Auditable origin shared by every word and segment in one chunk."""

    engine: SpeechEngineIdentity
    request_id: Identifier
    project_id: ProjectId
    media_asset_id: MediaAssetId
    source_audio_sha256: Sha256
    language: LanguageTag
    full_audio_range: AudioSampleRange
    chunk_audio_range: AudioSampleRange
    channel_index: int = Field(ge=0, le=255)
    chunk_index: int = Field(ge=0)
    chunk_count: int = Field(ge=1)

    @classmethod
    def from_request(
        cls,
        request: SpeechRecognitionRequest,
        engine: SpeechEngineIdentity,
    ) -> RecognitionProvenance:
        """Build provenance without copying unvalidated boundary dictionaries."""

        return cls(
            engine=engine,
            request_id=request.request_id,
            project_id=request.project_id,
            media_asset_id=request.media_asset_id,
            source_audio_sha256=request.source_audio_sha256,
            language=request.language,
            full_audio_range=request.full_audio_range,
            chunk_audio_range=request.audio_range,
            channel_index=request.channel_index,
            chunk_index=request.chunk_index,
            chunk_count=request.chunk_count,
        )


class RecognizedWord(SpeechContractModel):
    """One recognized lexical or punctuation token with exact sample timing."""

    word_id: Identifier
    text: WordText
    audio_range: AudioSampleRange
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    provenance: RecognitionProvenance

    @model_validator(mode="after")
    def _validate_word(self) -> Self:
        if self.audio_range.is_empty:
            raise ValueError("recognized word range cannot be empty")
        if self.audio_range.sample_rate != self.provenance.chunk_audio_range.sample_rate:
            raise ValueError("word and provenance use different sample rates")
        chunk_start = self.provenance.chunk_audio_range.start.sample_index
        chunk_end = self.provenance.chunk_audio_range.end_exclusive.sample_index
        word_start = self.audio_range.start.sample_index
        word_end = self.audio_range.end_exclusive.sample_index
        if word_start < chunk_start or word_end > chunk_end:
            raise ValueError("recognized word must be contained in its source chunk")
        return self


class RecognizedSegment(SpeechContractModel):
    """A recognizer segment whose words are monotonic and share provenance."""

    segment_id: Identifier
    text: SpeechText
    audio_range: AudioSampleRange
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    words: tuple[RecognizedWord, ...] = Field(min_length=1)
    provenance: RecognitionProvenance

    @model_validator(mode="after")
    def _validate_segment(self) -> Self:
        if self.audio_range.is_empty:
            raise ValueError("recognized segment range cannot be empty")
        if self.audio_range.sample_rate != self.provenance.chunk_audio_range.sample_rate:
            raise ValueError("segment and provenance use different sample rates")
        segment_start = self.audio_range.start.sample_index
        segment_end = self.audio_range.end_exclusive.sample_index
        previous_end = segment_start
        for word in self.words:
            if word.provenance != self.provenance:
                raise ValueError("segment words must share segment provenance")
            word_start = word.audio_range.start.sample_index
            word_end = word.audio_range.end_exclusive.sample_index
            if word_start < segment_start or word_end > segment_end:
                raise ValueError("segment word must be contained in the segment range")
            if word_start < previous_end:
                raise ValueError("segment word timing must be monotonic and non-overlapping")
            previous_end = word_end
        return self


class RecognitionWarning(SpeechContractModel):
    code: Identifier
    message: SpeechText
    audio_range: AudioSampleRange | None = None


class RecognitionChunkResult(SpeechContractModel):
    """Validated output for exactly one recognition request chunk."""

    provenance: RecognitionProvenance
    segments: tuple[RecognizedSegment, ...] = ()
    warnings: tuple[RecognitionWarning, ...] = ()

    @model_validator(mode="after")
    def _validate_result(self) -> Self:
        previous_end = self.provenance.chunk_audio_range.start.sample_index
        for segment in self.segments:
            if segment.provenance != self.provenance:
                raise ValueError("result segments must share result provenance")
            segment_start = segment.audio_range.start.sample_index
            if segment_start < previous_end:
                raise ValueError("result segment timing must be monotonic and non-overlapping")
            previous_end = segment.audio_range.end_exclusive.sample_index
        return self

    @property
    def words(self) -> tuple[RecognizedWord, ...]:
        return tuple(word for segment in self.segments for word in segment.words)


class RecognitionPhase(StrEnum):
    PLANNING = "planning"
    RECOGNIZING = "recognizing"
    MERGING = "merging"
    COMPLETE = "complete"


class RecognitionProgress(SpeechContractModel):
    request_id: Identifier
    phase: RecognitionPhase
    completed_samples: int = Field(ge=0)
    total_samples: int = Field(gt=0)
    chunk_index: int | None = Field(default=None, ge=0)
    chunk_count: int = Field(ge=1)

    @model_validator(mode="after")
    def _validate_progress(self) -> Self:
        if self.completed_samples > self.total_samples:
            raise ValueError("completed samples cannot exceed total samples")
        if self.chunk_index is not None and self.chunk_index >= self.chunk_count:
            raise ValueError("progress chunk index must be less than chunk count")
        return self


__all__ = [
    "RecognitionChunkResult",
    "RecognitionPhase",
    "RecognitionProgress",
    "RecognitionProvenance",
    "RecognitionWarning",
    "RecognizedSegment",
    "RecognizedWord",
    "SpeechContractModel",
    "SpeechEngineIdentity",
    "SpeechRecognitionRequest",
    "SpeechText",
    "WordText",
]
