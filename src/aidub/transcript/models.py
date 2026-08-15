"""Immutable transcript aggregate and mutation facts."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from aidub.application.invalidation import ArtifactStage
from aidub.domain import MediaAssetId, ProjectId, Utterance, UtteranceId
from aidub.domain.base import DomainModel, UtcDatetime
from aidub.domain.types import LanguageTag, NonEmptyStr, require_unique


class Transcript(DomainModel):
    """A chronologically ordered, versioned source-transcript snapshot."""

    project_id: ProjectId
    media_asset_id: MediaAssetId
    language: LanguageTag
    revision: int = Field(default=0, ge=0)
    utterances: tuple[Utterance, ...] = ()

    @model_validator(mode="after")
    def _validate_scope_and_order(self) -> Self:
        require_unique(
            tuple(line.utterance_id for line in self.utterances),
            field_name="utterance_ids",
        )
        previous: Utterance | None = None
        for line in self.utterances:
            if line.project_id != self.project_id:
                raise ValueError("every utterance must belong to the transcript project")
            if line.source_language.casefold() != self.language.casefold():
                raise ValueError("every utterance must use the transcript source language")
            if previous is not None and line.source_range.start < previous.source_range.start:
                raise ValueError("utterances must be ordered by source start time")
            previous = line
        return self

    def index_of(self, utterance_id: str) -> int:
        """Return an utterance index, or ``-1`` when it is absent."""

        return next(
            (
                index
                for index, utterance in enumerate(self.utterances)
                if utterance.utterance_id == utterance_id
            ),
            -1,
        )


class TranscriptOperation(StrEnum):
    EDIT_TEXT = "edit_text"
    LOCK_FIELDS = "lock_fields"
    UNLOCK_FIELDS = "unlock_fields"
    AUTOMATED_ASR_UPDATE = "automated_asr_update"
    SPLIT = "split"
    MERGE = "merge"
    ASSIGN_SPEAKER = "assign_speaker"
    ASSIGN_CHARACTER = "assign_character"
    CHANGE_STATUS = "change_status"
    APPROVE = "approve"


class TranscriptAuditFact(DomainModel):
    """Persistable fact emitted for every accepted transcript mutation."""

    operation: TranscriptOperation
    actor: NonEmptyStr
    occurred_at: UtcDatetime
    expected_revision: int = Field(ge=0)
    new_revision: int = Field(ge=1)
    affected_utterance_ids: tuple[UtteranceId, ...]
    automated: bool = False

    @model_validator(mode="after")
    def _validate_revision_and_ids(self) -> Self:
        if self.new_revision != self.expected_revision + 1:
            raise ValueError("an audit fact must describe exactly one aggregate revision")
        require_unique(self.affected_utterance_ids, field_name="affected_utterance_ids")
        if not self.affected_utterance_ids:
            raise ValueError("a mutation must affect at least one utterance")
        return self


class InvalidationRoot(DomainModel):
    """Deterministic root consumed by the dependency graph for downstream invalidation."""

    key: NonEmptyStr
    stage: ArtifactStage
    project_id: ProjectId
    media_asset_id: MediaAssetId
    language: LanguageTag
    utterance_id: UtteranceId

    @model_validator(mode="after")
    def _validate_key(self) -> Self:
        expected = invalidation_key(
            stage=self.stage,
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            language=self.language,
            utterance_id=self.utterance_id,
        )
        if self.key != expected:
            raise ValueError("invalidation key does not match its typed scope")
        return self


class TranscriptMutationResult(DomainModel):
    """A new snapshot plus auditable effects; the input snapshot remains untouched."""

    transcript: Transcript
    audit: TranscriptAuditFact
    invalidation_roots: tuple[InvalidationRoot, ...] = ()


def invalidation_key(
    *,
    stage: ArtifactStage,
    project_id: str,
    media_asset_id: str,
    language: str,
    utterance_id: str,
) -> str:
    """Build a stable, locale-independent dependency identifier."""

    return ":".join(
        (
            stage.value,
            project_id,
            media_asset_id,
            language.casefold(),
            utterance_id,
        )
    )


__all__ = [
    "InvalidationRoot",
    "Transcript",
    "TranscriptAuditFact",
    "TranscriptMutationResult",
    "TranscriptOperation",
    "invalidation_key",
]
