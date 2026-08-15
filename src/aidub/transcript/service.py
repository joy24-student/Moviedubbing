"""Optimistic, snapshot-based transcript command service."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import ValidationError

from aidub.application.invalidation import ArtifactStage
from aidub.domain import (
    AudioSamplePosition,
    AudioSampleRange,
    LockedUtteranceField,
    RationalTime,
    TimeRange,
    Utterance,
    UtteranceStatus,
    WordTiming,
)

from .commands import (
    ApproveUtteranceCommand,
    AssignCharacterCommand,
    AssignSpeakerCommand,
    AutomatedAsrUpdateCommand,
    ChangeStatusCommand,
    EditTextCommand,
    LockFieldsCommand,
    MergePolicy,
    MergeUtterancesCommand,
    SplitUtteranceCommand,
    TranscriptCommand,
    UnlockFieldsCommand,
)
from .errors import (
    LockedFieldViolation,
    TranscriptInvariantViolation,
    TranscriptRevisionConflict,
    UtteranceNotFound,
)
from .models import (
    InvalidationRoot,
    Transcript,
    TranscriptAuditFact,
    TranscriptMutationResult,
    TranscriptOperation,
    invalidation_key,
)

_CONTENT_LOCKS = frozenset(
    {
        LockedUtteranceField.SOURCE_TEXT,
        LockedUtteranceField.SOURCE_TIMING,
        LockedUtteranceField.EDIT_TIMING,
    }
)

_STATUS_TRANSITIONS: dict[UtteranceStatus, frozenset[UtteranceStatus]] = {
    UtteranceStatus.DRAFT: frozenset(
        {UtteranceStatus.REVIEW, UtteranceStatus.LOCKED, UtteranceStatus.STALE}
    ),
    UtteranceStatus.REVIEW: frozenset(
        {UtteranceStatus.DRAFT, UtteranceStatus.LOCKED, UtteranceStatus.STALE}
    ),
    UtteranceStatus.APPROVED: frozenset({UtteranceStatus.STALE}),
    UtteranceStatus.LOCKED: frozenset(
        {UtteranceStatus.DRAFT, UtteranceStatus.REVIEW, UtteranceStatus.STALE}
    ),
    UtteranceStatus.STALE: frozenset({UtteranceStatus.DRAFT, UtteranceStatus.REVIEW}),
}


class TranscriptCommandService:
    """Apply commands to immutable snapshots with aggregate-level compare-and-swap semantics."""

    def apply(
        self,
        transcript: Transcript,
        command: TranscriptCommand,
    ) -> TranscriptMutationResult:
        """Dispatch one typed editor command without weakening command-specific validation."""

        if isinstance(command, EditTextCommand):
            return self.edit_text(transcript, command)
        if isinstance(command, LockFieldsCommand):
            return self.lock_fields(transcript, command)
        if isinstance(command, UnlockFieldsCommand):
            return self.unlock_fields(transcript, command)
        if isinstance(command, AutomatedAsrUpdateCommand):
            return self.apply_automated_asr_update(transcript, command)
        if isinstance(command, SplitUtteranceCommand):
            return self.split(transcript, command)
        if isinstance(command, MergeUtterancesCommand):
            return self.merge(transcript, command)
        if isinstance(command, AssignSpeakerCommand):
            return self.assign_speaker(transcript, command)
        if isinstance(command, AssignCharacterCommand):
            return self.assign_character(transcript, command)
        if isinstance(command, ChangeStatusCommand):
            return self.change_status(transcript, command)
        if isinstance(command, ApproveUtteranceCommand):
            return self.approve(transcript, command)
        raise TypeError(f"unsupported transcript command: {type(command).__name__}")

    def edit_text(
        self,
        transcript: Transcript,
        command: EditTextCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        self._require_unlocked(line, {LockedUtteranceField.SOURCE_TEXT})
        if command.source_text == line.source_text:
            raise TranscriptInvariantViolation("text edit does not change the utterance")
        updated = self._updated_line(
            line,
            source_text=command.source_text,
            status=self._status_after_content_change(line.status),
        )
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.EDIT_TEXT,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
            invalidation_stage=ArtifactStage.TRANSCRIPT,
        )

    def lock_fields(
        self,
        transcript: Transcript,
        command: LockFieldsCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        locked_fields = line.locked_fields | command.fields
        if locked_fields == line.locked_fields:
            raise TranscriptInvariantViolation("all requested fields are already locked")
        updated = self._updated_line(line, locked_fields=locked_fields)
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.LOCK_FIELDS,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
        )

    def unlock_fields(
        self,
        transcript: Transcript,
        command: UnlockFieldsCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        removed = line.locked_fields & command.fields
        if not removed:
            raise TranscriptInvariantViolation("none of the requested fields are locked")
        locked_fields = line.locked_fields - command.fields
        if line.status is UtteranceStatus.LOCKED and not locked_fields:
            raise TranscriptInvariantViolation(
                "change the locked workflow status before removing its final field lock"
            )
        updated = self._updated_line(line, locked_fields=locked_fields)
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.UNLOCK_FIELDS,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
        )

    def apply_automated_asr_update(
        self,
        transcript: Transcript,
        command: AutomatedAsrUpdateCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        changes: dict[str, object] = {}

        if command.source_text is not None and command.source_text != line.source_text:
            self._require_unlocked(line, {LockedUtteranceField.SOURCE_TEXT})
            changes["source_text"] = command.source_text
        if command.source_range is not None and command.source_range != line.source_range:
            self._require_unlocked(line, {LockedUtteranceField.SOURCE_TIMING})
            changes["source_range"] = command.source_range
        if command.words is not None and command.words != line.words:
            self._require_unlocked(line, {LockedUtteranceField.SOURCE_TIMING})
            changes["words"] = command.words
        if command.edit_range is not None and command.edit_range != line.edit_range:
            self._require_unlocked(line, {LockedUtteranceField.EDIT_TIMING})
            changes["edit_range"] = command.edit_range
        if command.confidence is not None and command.confidence != line.confidence:
            changes["confidence"] = command.confidence

        if not changes:
            raise TranscriptInvariantViolation("automated ASR update has no effective change")
        changes["status"] = self._status_after_content_change(line.status)
        updated = self._updated_line(line, **changes)
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.AUTOMATED_ASR_UPDATE,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
            invalidation_stage=ArtifactStage.TRANSCRIPT,
            automated=True,
        )

    def split(
        self,
        transcript: Transcript,
        command: SplitUtteranceCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        self._require_unlocked(line, _CONTENT_LOCKS)
        self._require_new_split_ids(transcript, command)

        try:
            left_source, right_source = line.source_range.split_at(command.source_position)
            left_edit, right_edit = line.edit_range.split_at(command.edit_position)
            left_audio, right_audio = self._split_audio_range(
                line.source_audio_range,
                source_range=line.source_range,
                source_position=command.source_position,
            )
        except ValueError as error:
            raise TranscriptInvariantViolation(str(error)) from error

        left_words, right_words = self._partition_words(line.words, command.source_position)
        next_revision = line.revision + 1
        left = self._updated_line(
            line,
            utterance_id=command.left_utterance_id,
            source_range=left_source,
            edit_range=left_edit,
            source_audio_range=left_audio,
            source_text=command.left_text,
            words=left_words,
            status=UtteranceStatus.DRAFT,
            revision=next_revision,
        )
        right = self._updated_line(
            line,
            utterance_id=command.right_utterance_id,
            source_range=right_source,
            edit_range=right_edit,
            source_audio_range=right_audio,
            source_text=command.right_text,
            words=right_words,
            status=UtteranceStatus.DRAFT,
            revision=next_revision,
        )
        utterances = (
            *transcript.utterances[:index],
            left,
            right,
            *transcript.utterances[index + 1 :],
        )
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.SPLIT,
            utterances=utterances,
            affected_ids=(
                line.utterance_id,
                left.utterance_id,
                right.utterance_id,
            ),
            invalidation_stage=ArtifactStage.TRANSCRIPT,
        )

    def merge(
        self,
        transcript: Transcript,
        command: MergeUtterancesCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        left_index, left = self._require_line(transcript, command.left_utterance_id)
        right_index, right = self._require_line(transcript, command.right_utterance_id)
        if right_index != left_index + 1:
            raise TranscriptInvariantViolation("merge candidates must be consecutive and ordered")
        if (
            command.merged_utterance_id
            in {
                left.utterance_id,
                right.utterance_id,
            }
            or transcript.index_of(command.merged_utterance_id) >= 0
        ):
            raise TranscriptInvariantViolation("merged utterance identifier must be new")
        self._require_unlocked(left, _CONTENT_LOCKS)
        self._require_unlocked(right, _CONTENT_LOCKS)
        self._require_merge_scope(transcript, left, right)
        self._require_merge_ranges(left.source_range, right.source_range, command.policy)
        self._require_merge_ranges(left.edit_range, right.edit_range, command.policy)
        self._require_merge_identity_locks(left, right)

        source_range = self._covering_range(left.source_range, right.source_range)
        edit_range = self._covering_range(left.edit_range, right.edit_range)
        audio_range = self._merge_audio_ranges(
            left.source_audio_range,
            right.source_audio_range,
            command.policy,
        )
        words = (*left.words, *right.words)
        next_revision = max(left.revision, right.revision) + 1
        merged = self._updated_line(
            left,
            utterance_id=command.merged_utterance_id,
            scene_id=left.scene_id if left.scene_id == right.scene_id else None,
            speaker_id=left.speaker_id if left.speaker_id == right.speaker_id else None,
            character_id=left.character_id if left.character_id == right.character_id else None,
            source_range=source_range,
            edit_range=edit_range,
            source_audio_range=audio_range,
            source_text=command.merged_text,
            confidence=min(left.confidence, right.confidence),
            words=words,
            emotion=left.emotion if left.emotion == right.emotion else None,
            prosody=left.prosody if left.prosody == right.prosody else None,
            visibility=left.visibility if left.visibility == right.visibility else None,
            status=UtteranceStatus.DRAFT,
            locked_fields=left.locked_fields | right.locked_fields,
            revision=next_revision,
        )
        utterances = (
            *transcript.utterances[:left_index],
            merged,
            *transcript.utterances[right_index + 1 :],
        )
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.MERGE,
            utterances=utterances,
            affected_ids=(
                left.utterance_id,
                right.utterance_id,
                merged.utterance_id,
            ),
            invalidation_stage=ArtifactStage.TRANSCRIPT,
        )

    def assign_speaker(
        self,
        transcript: Transcript,
        command: AssignSpeakerCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        self._require_unlocked(line, {LockedUtteranceField.SPEAKER})
        if command.speaker_id == line.speaker_id:
            raise TranscriptInvariantViolation("speaker assignment does not change the utterance")
        updated = self._updated_line(
            line,
            speaker_id=command.speaker_id,
            status=self._status_after_content_change(line.status),
        )
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.ASSIGN_SPEAKER,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
            invalidation_stage=ArtifactStage.DIARIZATION,
        )

    def assign_character(
        self,
        transcript: Transcript,
        command: AssignCharacterCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        self._require_unlocked(line, {LockedUtteranceField.CHARACTER})
        if command.character_id == line.character_id:
            raise TranscriptInvariantViolation("character assignment does not change the utterance")
        updated = self._updated_line(
            line,
            character_id=command.character_id,
            status=self._status_after_content_change(line.status),
        )
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.ASSIGN_CHARACTER,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
            invalidation_stage=ArtifactStage.DIARIZATION,
        )

    def change_status(
        self,
        transcript: Transcript,
        command: ChangeStatusCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        if command.status is UtteranceStatus.APPROVED:
            raise TranscriptInvariantViolation("use the approval command to approve an utterance")
        allowed = _STATUS_TRANSITIONS[line.status]
        if command.status not in allowed:
            raise TranscriptInvariantViolation(
                f"cannot change utterance status from {line.status} to {command.status}"
            )
        if command.status is UtteranceStatus.LOCKED and not line.locked_fields:
            raise TranscriptInvariantViolation("locked status requires at least one field lock")
        updated = self._updated_line(line, status=command.status)
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.CHANGE_STATUS,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
        )

    def approve(
        self,
        transcript: Transcript,
        command: ApproveUtteranceCommand,
    ) -> TranscriptMutationResult:
        self._require_revision(transcript, command)
        index, line = self._require_line(transcript, command.utterance_id)
        if line.status is not UtteranceStatus.REVIEW:
            raise TranscriptInvariantViolation("only an utterance in review can be approved")
        updated = self._updated_line(line, status=UtteranceStatus.APPROVED)
        return self._finish(
            transcript,
            command,
            operation=TranscriptOperation.APPROVE,
            utterances=self._replace(transcript.utterances, index, updated),
            affected_ids=(line.utterance_id,),
        )

    @staticmethod
    def _require_revision(transcript: Transcript, command: TranscriptCommand) -> None:
        if command.expected_revision != transcript.revision:
            raise TranscriptRevisionConflict(
                expected=command.expected_revision,
                current=transcript.revision,
            )

    @staticmethod
    def _require_line(transcript: Transcript, utterance_id: str) -> tuple[int, Utterance]:
        index = transcript.index_of(utterance_id)
        if index < 0:
            raise UtteranceNotFound(f"utterance is not in this transcript: {utterance_id}")
        return index, transcript.utterances[index]

    @staticmethod
    def _require_unlocked(
        line: Utterance,
        fields: Iterable[LockedUtteranceField],
    ) -> None:
        conflicts = line.locked_fields & frozenset(fields)
        if conflicts:
            names = ", ".join(sorted(field.value for field in conflicts))
            raise LockedFieldViolation(f"utterance fields are locked: {names}")

    @staticmethod
    def _updated_line(line: Utterance, **changes: object) -> Utterance:
        values: dict[str, object] = line.model_dump(mode="python")
        values.update(changes)
        if "revision" not in changes:
            values["revision"] = line.revision + 1
        try:
            return Utterance.model_validate(values)
        except ValidationError as error:
            raise TranscriptInvariantViolation(str(error)) from error

    @staticmethod
    def _replace(
        utterances: tuple[Utterance, ...],
        index: int,
        line: Utterance,
    ) -> tuple[Utterance, ...]:
        return (*utterances[:index], line, *utterances[index + 1 :])

    @staticmethod
    def _status_after_content_change(status: UtteranceStatus) -> UtteranceStatus:
        if status is UtteranceStatus.APPROVED:
            return UtteranceStatus.STALE
        return status

    @staticmethod
    def _require_new_split_ids(
        transcript: Transcript,
        command: SplitUtteranceCommand,
    ) -> None:
        proposed = {
            command.utterance_id,
            command.left_utterance_id,
            command.right_utterance_id,
        }
        if len(proposed) != 3:
            raise TranscriptInvariantViolation("split output identifiers must be new and distinct")
        existing = {line.utterance_id for line in transcript.utterances}
        if command.left_utterance_id in existing or command.right_utterance_id in existing:
            raise TranscriptInvariantViolation("split output identifier already exists")

    @staticmethod
    def _partition_words(
        words: tuple[WordTiming, ...],
        position: RationalTime,
    ) -> tuple[tuple[WordTiming, ...], tuple[WordTiming, ...]]:
        left: list[WordTiming] = []
        right: list[WordTiming] = []
        for word in words:
            if word.source_range.end_exclusive <= position:
                left.append(word)
            elif position <= word.source_range.start:
                right.append(word)
            else:
                raise TranscriptInvariantViolation(
                    f"split position crosses aligned word {word.text!r}"
                )
        return tuple(left), tuple(right)

    @staticmethod
    def _split_audio_range(
        audio_range: AudioSampleRange | None,
        *,
        source_range: TimeRange,
        source_position: RationalTime,
    ) -> tuple[AudioSampleRange | None, AudioSampleRange | None]:
        if audio_range is None:
            return None, None
        elapsed = source_position.seconds - source_range.start.seconds
        offset = elapsed * audio_range.sample_rate
        if offset.denominator != 1:
            raise ValueError("source split is not exactly representable in the audio sample clock")
        sample_offset = offset.numerator
        if not 0 < sample_offset < audio_range.sample_count:
            raise ValueError("source split lies outside the mapped audio sample range")
        split_index = audio_range.start.sample_index + sample_offset
        left = AudioSampleRange(start=audio_range.start, sample_count=sample_offset)
        right = AudioSampleRange(
            start=AudioSamplePosition(
                sample_index=split_index,
                sample_rate=audio_range.sample_rate,
            ),
            sample_count=audio_range.sample_count - sample_offset,
        )
        return left, right

    @staticmethod
    def _require_merge_scope(
        transcript: Transcript,
        left: Utterance,
        right: Utterance,
    ) -> None:
        if left.project_id != right.project_id or left.project_id != transcript.project_id:
            raise TranscriptInvariantViolation("merge candidates must belong to the same project")
        if (
            left.source_language.casefold() != right.source_language.casefold()
            or left.source_language.casefold() != transcript.language.casefold()
        ):
            raise TranscriptInvariantViolation("merge candidates must use the same language")

    @staticmethod
    def _require_merge_ranges(
        left: TimeRange,
        right: TimeRange,
        policy: MergePolicy,
    ) -> None:
        adjacent = left.end_exclusive == right.start
        if policy is MergePolicy.ADJACENT_ONLY and not adjacent:
            raise TranscriptInvariantViolation("adjacent-only merge requires touching ranges")
        if policy is MergePolicy.ALLOW_OVERLAP and not (adjacent or left.overlaps(right)):
            raise TranscriptInvariantViolation("overlap merge does not permit a timeline gap")

    @classmethod
    def _merge_audio_ranges(
        cls,
        left: AudioSampleRange | None,
        right: AudioSampleRange | None,
        policy: MergePolicy,
    ) -> AudioSampleRange | None:
        if left is None and right is None:
            return None
        if left is None or right is None:
            raise TranscriptInvariantViolation(
                "merge candidates must both have audio sample ranges or both omit them"
            )
        if left.sample_rate != right.sample_rate:
            raise TranscriptInvariantViolation("audio sample ranges use different rates")
        adjacent = left.end_exclusive == right.start
        if policy is MergePolicy.ADJACENT_ONLY and not adjacent:
            raise TranscriptInvariantViolation("adjacent-only merge requires touching audio ranges")
        if policy is MergePolicy.ALLOW_OVERLAP and not (adjacent or left.overlaps(right)):
            raise TranscriptInvariantViolation("overlap merge does not permit an audio gap")
        start_index = min(left.start.sample_index, right.start.sample_index)
        end_index = max(left.end_exclusive.sample_index, right.end_exclusive.sample_index)
        return AudioSampleRange(
            start=AudioSamplePosition(
                sample_index=start_index,
                sample_rate=left.sample_rate,
            ),
            sample_count=end_index - start_index,
        )

    @staticmethod
    def _covering_range(left: TimeRange, right: TimeRange) -> TimeRange:
        rate = RationalTime.common_rate(left.rate, right.rate)
        converted_left = left.rescaled_to(rate)
        converted_right = right.rescaled_to(rate)
        return TimeRange.from_start_end(
            min(converted_left.start, converted_right.start),
            max(converted_left.end_exclusive, converted_right.end_exclusive),
        )

    @staticmethod
    def _require_merge_identity_locks(left: Utterance, right: Utterance) -> None:
        if left.speaker_id != right.speaker_id and (
            LockedUtteranceField.SPEAKER in left.locked_fields
            or LockedUtteranceField.SPEAKER in right.locked_fields
        ):
            raise LockedFieldViolation("merge would clear a locked speaker assignment")
        if left.character_id != right.character_id and (
            LockedUtteranceField.CHARACTER in left.locked_fields
            or LockedUtteranceField.CHARACTER in right.locked_fields
        ):
            raise LockedFieldViolation("merge would clear a locked character assignment")

    @staticmethod
    def _finish(
        transcript: Transcript,
        command: TranscriptCommand,
        *,
        operation: TranscriptOperation,
        utterances: tuple[Utterance, ...],
        affected_ids: tuple[str, ...],
        invalidation_stage: ArtifactStage | None = None,
        automated: bool = False,
    ) -> TranscriptMutationResult:
        values: dict[str, object] = transcript.model_dump(mode="python")
        values.update(revision=transcript.revision + 1, utterances=utterances)
        try:
            updated_transcript = Transcript.model_validate(values)
        except ValidationError as error:
            raise TranscriptInvariantViolation(str(error)) from error

        audit = TranscriptAuditFact(
            operation=operation,
            actor=command.actor,
            occurred_at=command.occurred_at,
            expected_revision=command.expected_revision,
            new_revision=updated_transcript.revision,
            affected_utterance_ids=affected_ids,
            automated=automated,
        )
        roots: tuple[InvalidationRoot, ...] = ()
        if invalidation_stage is not None:
            roots = tuple(
                InvalidationRoot(
                    key=invalidation_key(
                        stage=invalidation_stage,
                        project_id=transcript.project_id,
                        media_asset_id=transcript.media_asset_id,
                        language=transcript.language,
                        utterance_id=utterance_id,
                    ),
                    stage=invalidation_stage,
                    project_id=transcript.project_id,
                    media_asset_id=transcript.media_asset_id,
                    language=transcript.language,
                    utterance_id=utterance_id,
                )
                for utterance_id in affected_ids
            )
        return TranscriptMutationResult(
            transcript=updated_transcript,
            audit=audit,
            invalidation_roots=roots,
        )


__all__ = ["TranscriptCommandService"]
