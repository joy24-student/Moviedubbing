"""Sample/frame-aware transcript utterances and word alignment."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel
from .identifiers import CharacterId, ProjectId, SceneId, SpeakerId, UtteranceId
from .time import AudioSampleRange, TimeRange
from .types import LanguageTag, LongText, NonEmptyStr


class UtteranceStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    LOCKED = "locked"
    STALE = "stale"


class LockedUtteranceField(StrEnum):
    SOURCE_TEXT = "source_text"
    SOURCE_TIMING = "source_timing"
    EDIT_TIMING = "edit_timing"
    SPEAKER = "speaker"
    CHARACTER = "character"
    EMOTION = "emotion"


class WordTiming(DomainModel):
    text: NonEmptyStr
    source_range: TimeRange
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _require_duration(self) -> Self:
        if self.source_range.is_empty:
            raise ValueError("word timing must have positive duration")
        return self


class Emotion(DomainModel):
    label: NonEmptyStr
    intensity: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)


class Prosody(DomainModel):
    rate: float = Field(default=1.0, gt=0.0, le=4.0, allow_inf_nan=False)
    energy: float = Field(default=1.0, ge=0.0, le=4.0, allow_inf_nan=False)
    pitch_semitones: float = Field(default=0.0, ge=-24.0, le=24.0, allow_inf_nan=False)


class FaceVisibilityPriority(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FaceVisibility(DomainModel):
    active_face_id: str | None = Field(default=None, min_length=1, max_length=68)
    priority: FaceVisibilityPriority = FaceVisibilityPriority.NONE
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _validate_face(self) -> Self:
        if self.active_face_id is None and self.priority is not FaceVisibilityPriority.NONE:
            raise ValueError("visible-face priority requires an active face identifier")
        if self.active_face_id is None and self.confidence is not None:
            raise ValueError("face confidence requires an active face identifier")
        return self


class Utterance(DomainModel):
    """Canonical source speech segment mapped into edit and audio clocks."""

    utterance_id: UtteranceId
    project_id: ProjectId
    scene_id: SceneId | None = None
    speaker_id: SpeakerId | None = None
    character_id: CharacterId | None = None
    source_range: TimeRange
    edit_range: TimeRange
    source_audio_range: AudioSampleRange | None = None
    source_text: LongText
    source_language: LanguageTag
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    words: tuple[WordTiming, ...] = ()
    emotion: Emotion | None = None
    prosody: Prosody | None = None
    visibility: FaceVisibility | None = None
    status: UtteranceStatus = UtteranceStatus.DRAFT
    locked_fields: frozenset[LockedUtteranceField] = frozenset()
    revision: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _validate_utterance(self) -> Self:
        if self.source_range.is_empty or self.edit_range.is_empty:
            raise ValueError("speech utterances must have positive source and edit duration")
        previous: WordTiming | None = None
        for word in self.words:
            if not self.source_range.contains_range(word.source_range):
                raise ValueError("word timing lies outside the utterance source range")
            if (
                previous is not None
                and word.source_range.start < previous.source_range.end_exclusive
            ):
                raise ValueError("word timings must be ordered and non-overlapping")
            previous = word
        if self.status is UtteranceStatus.LOCKED and not self.locked_fields:
            raise ValueError("a locked utterance must identify at least one locked field")
        return self


__all__ = [
    "Emotion",
    "FaceVisibility",
    "FaceVisibilityPriority",
    "LockedUtteranceField",
    "Prosody",
    "Utterance",
    "UtteranceStatus",
    "WordTiming",
]
