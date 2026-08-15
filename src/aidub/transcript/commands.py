"""Strict commands accepted by the transcript editor."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from aidub.domain import (
    CharacterId,
    LockedUtteranceField,
    SpeakerId,
    TimeRange,
    UtteranceId,
    UtteranceStatus,
    WordTiming,
)
from aidub.domain.base import DomainModel, UtcDatetime, utc_now
from aidub.domain.time import RationalTime
from aidub.domain.types import LongText, NonEmptyStr


class TranscriptCommand(DomainModel):
    expected_revision: int = Field(ge=0)
    actor: NonEmptyStr
    occurred_at: UtcDatetime = Field(default_factory=utc_now)


class EditTextCommand(TranscriptCommand):
    utterance_id: UtteranceId
    source_text: LongText


class LockFieldsCommand(TranscriptCommand):
    utterance_id: UtteranceId
    fields: frozenset[LockedUtteranceField] = Field(min_length=1)


class UnlockFieldsCommand(TranscriptCommand):
    utterance_id: UtteranceId
    fields: frozenset[LockedUtteranceField] = Field(min_length=1)


class AutomatedAsrUpdateCommand(TranscriptCommand):
    """Partial machine update; ``None`` means the ASR provider did not propose the field."""

    utterance_id: UtteranceId
    source_text: LongText | None = None
    source_range: TimeRange | None = None
    edit_range: TimeRange | None = None
    words: tuple[WordTiming, ...] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _require_proposal(self) -> Self:
        if all(
            value is None
            for value in (
                self.source_text,
                self.source_range,
                self.edit_range,
                self.words,
                self.confidence,
            )
        ):
            raise ValueError("an automated ASR update must propose at least one field")
        return self


class SplitUtteranceCommand(TranscriptCommand):
    utterance_id: UtteranceId
    left_utterance_id: UtteranceId
    right_utterance_id: UtteranceId
    source_position: RationalTime
    edit_position: RationalTime
    left_text: LongText
    right_text: LongText


class MergePolicy(StrEnum):
    ADJACENT_ONLY = "adjacent_only"
    ALLOW_OVERLAP = "allow_overlap"


class MergeUtterancesCommand(TranscriptCommand):
    left_utterance_id: UtteranceId
    right_utterance_id: UtteranceId
    merged_utterance_id: UtteranceId
    merged_text: LongText
    policy: MergePolicy = MergePolicy.ADJACENT_ONLY


class AssignSpeakerCommand(TranscriptCommand):
    utterance_id: UtteranceId
    speaker_id: SpeakerId | None


class AssignCharacterCommand(TranscriptCommand):
    utterance_id: UtteranceId
    character_id: CharacterId | None


class ChangeStatusCommand(TranscriptCommand):
    utterance_id: UtteranceId
    status: UtteranceStatus


class ApproveUtteranceCommand(TranscriptCommand):
    utterance_id: UtteranceId


__all__ = [
    "ApproveUtteranceCommand",
    "AssignCharacterCommand",
    "AssignSpeakerCommand",
    "AutomatedAsrUpdateCommand",
    "ChangeStatusCommand",
    "EditTextCommand",
    "LockFieldsCommand",
    "MergePolicy",
    "MergeUtterancesCommand",
    "SplitUtteranceCommand",
    "TranscriptCommand",
    "UnlockFieldsCommand",
]
