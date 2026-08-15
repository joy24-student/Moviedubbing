"""Deterministic merging of overlapping speech-recognition chunks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from unicodedata import normalize

from pydantic import Field, model_validator

from aidub.contracts.base import Identifier
from aidub.domain.identifiers import MediaAssetId, ProjectId
from aidub.domain.time import AudioSampleRange
from aidub.domain.types import LanguageTag, Sha256

from .chunking import AudioChunkPlan
from .contracts import (
    RecognitionChunkResult,
    RecognizedWord,
    SpeechContractModel,
    SpeechEngineIdentity,
    SpeechText,
)


class MergeCompatibilityError(ValueError):
    """Raised before outputs from incompatible clocks or sources can be combined."""


class MergeWarningCode(StrEnum):
    OVERLAP_DUPLICATE_REMOVED = "overlap_duplicate_removed"
    OVERLAPPING_TIMING_CONFLICT = "overlapping_timing_conflict"


class MergeWarning(SpeechContractModel):
    code: MergeWarningCode
    message: SpeechText
    kept_word_id: Identifier
    dropped_word_id: Identifier
    audio_range: AudioSampleRange


class MergedTranscript(SpeechContractModel):
    """Monotonic words retained verbatim from compatible chunk results."""

    request_id: Identifier
    project_id: ProjectId
    media_asset_id: MediaAssetId
    source_audio_sha256: Sha256
    language: LanguageTag
    channel_index: int = Field(ge=0, le=255)
    audio_range: AudioSampleRange
    engine: SpeechEngineIdentity
    chunk_count: int = Field(ge=1)
    words: tuple[RecognizedWord, ...] = ()
    warnings: tuple[MergeWarning, ...] = ()

    @model_validator(mode="after")
    def _validate_words(self) -> MergedTranscript:
        previous_end = self.audio_range.start.sample_index
        for word in self.words:
            provenance = word.provenance
            if provenance.request_id != self.request_id:
                raise ValueError("merged word request provenance does not match transcript")
            if provenance.project_id != self.project_id:
                raise ValueError("merged word project provenance does not match transcript")
            if provenance.media_asset_id != self.media_asset_id:
                raise ValueError("merged word media provenance does not match transcript")
            if provenance.source_audio_sha256 != self.source_audio_sha256:
                raise ValueError("merged word source hash does not match transcript")
            if provenance.language != self.language:
                raise ValueError("merged word language does not match transcript")
            if provenance.channel_index != self.channel_index:
                raise ValueError("merged word channel does not match transcript")
            if provenance.engine != self.engine:
                raise ValueError("merged word engine provenance does not match transcript")
            if word.audio_range.sample_rate != self.audio_range.sample_rate:
                raise ValueError("merged word and transcript use different sample rates")
            word_start = word.audio_range.start.sample_index
            word_end = word.audio_range.end_exclusive.sample_index
            if word_start < self.audio_range.start.sample_index:
                raise ValueError("merged word starts before the transcript range")
            if word_end > self.audio_range.end_exclusive.sample_index:
                raise ValueError("merged word ends after the transcript range")
            if word_start < previous_end:
                raise ValueError("merged word timing must be monotonic and non-overlapping")
            previous_end = word_end
        return self


@dataclass(frozen=True, slots=True)
class _Candidate:
    word: RecognizedWord
    sequence: int

    @property
    def chunk_index(self) -> int:
        return self.word.provenance.chunk_index


class DeterministicChunkMerger:
    """Resolve overlap duplicates without ever moving a timestamp."""

    def merge(
        self,
        plan: AudioChunkPlan,
        results: tuple[RecognitionChunkResult, ...],
    ) -> MergedTranscript:
        ordered_results = self._validate_and_order(plan, results)
        baseline = ordered_results[0].provenance
        candidates = [
            _Candidate(word=word, sequence=sequence)
            for sequence, word in enumerate(
                word for result in ordered_results for word in result.words
            )
        ]
        candidates.sort(key=_chronological_key)

        kept: list[_Candidate] = []
        warnings: list[MergeWarning] = []
        for candidate in candidates:
            survivor: _Candidate | None = candidate
            while survivor is not None and kept and _overlaps(kept[-1].word, survivor.word):
                incumbent = kept[-1]
                winner, loser = _choose_winner(incumbent, survivor)
                duplicate = incumbent.chunk_index != survivor.chunk_index and _normalized_text(
                    incumbent.word.text
                ) == _normalized_text(survivor.word.text)
                code = (
                    MergeWarningCode.OVERLAP_DUPLICATE_REMOVED
                    if duplicate
                    else MergeWarningCode.OVERLAPPING_TIMING_CONFLICT
                )
                warnings.append(
                    MergeWarning(
                        code=code,
                        message=(
                            "Removed a duplicate token from overlapping chunks"
                            if duplicate
                            else "Dropped an overlapping token to preserve monotonic timing; "
                            "no timestamp was shifted"
                        ),
                        kept_word_id=winner.word.word_id,
                        dropped_word_id=loser.word.word_id,
                        audio_range=loser.word.audio_range,
                    )
                )
                if winner is incumbent:
                    survivor = None
                else:
                    kept.pop()
                    survivor = winner
            if survivor is not None:
                kept.append(survivor)

        return MergedTranscript(
            request_id=baseline.request_id,
            project_id=baseline.project_id,
            media_asset_id=baseline.media_asset_id,
            source_audio_sha256=baseline.source_audio_sha256,
            language=baseline.language,
            channel_index=baseline.channel_index,
            audio_range=plan.source_range,
            engine=baseline.engine,
            chunk_count=len(plan.chunks),
            words=tuple(candidate.word for candidate in kept),
            warnings=tuple(warnings),
        )

    def _validate_and_order(
        self,
        plan: AudioChunkPlan,
        results: tuple[RecognitionChunkResult, ...],
    ) -> tuple[RecognitionChunkResult, ...]:
        if len(results) != len(plan.chunks):
            raise MergeCompatibilityError("result count does not match the chunk plan")

        by_index: dict[int, RecognitionChunkResult] = {}
        for result in results:
            index = result.provenance.chunk_index
            if index in by_index:
                raise MergeCompatibilityError(f"duplicate result for chunk {index}")
            by_index[index] = result
        if set(by_index) != set(range(len(plan.chunks))):
            raise MergeCompatibilityError("result chunk indices do not match the chunk plan")

        ordered = tuple(by_index[index] for index in range(len(plan.chunks)))
        baseline = ordered[0].provenance
        for planned, result in zip(plan.chunks, ordered, strict=True):
            provenance = result.provenance
            if provenance.request_id != baseline.request_id:
                raise MergeCompatibilityError("cannot merge different recognition requests")
            if provenance.project_id != baseline.project_id:
                raise MergeCompatibilityError("cannot merge results from different projects")
            if provenance.media_asset_id != baseline.media_asset_id:
                raise MergeCompatibilityError("cannot merge results from different media sources")
            if provenance.source_audio_sha256 != baseline.source_audio_sha256:
                raise MergeCompatibilityError("cannot merge results with different source hashes")
            if provenance.language != baseline.language:
                raise MergeCompatibilityError("cannot merge results with different languages")
            if provenance.channel_index != baseline.channel_index:
                raise MergeCompatibilityError("cannot merge results from different audio channels")
            if provenance.engine != baseline.engine:
                raise MergeCompatibilityError("cannot merge results from different model builds")
            if provenance.chunk_count != len(plan.chunks):
                raise MergeCompatibilityError("result chunk count does not match the chunk plan")
            if provenance.full_audio_range != plan.source_range:
                raise MergeCompatibilityError("result source range does not match the chunk plan")
            if provenance.chunk_audio_range != planned.audio_range:
                raise MergeCompatibilityError(
                    f"result audio range does not match planned chunk {planned.index}"
                )
            if provenance.chunk_audio_range.sample_rate != plan.policy.sample_rate:
                raise MergeCompatibilityError("cannot merge results from different sample clocks")
        return ordered


def _chronological_key(candidate: _Candidate) -> tuple[int, int, int, int, str]:
    word = candidate.word
    return (
        word.audio_range.start.sample_index,
        word.audio_range.end_exclusive.sample_index,
        candidate.chunk_index,
        candidate.sequence,
        word.word_id,
    )


def _overlaps(left: RecognizedWord, right: RecognizedWord) -> bool:
    if left.audio_range.sample_rate != right.audio_range.sample_rate:
        raise MergeCompatibilityError("cannot compare words from different sample clocks")
    return (
        left.audio_range.start.sample_index < right.audio_range.end_exclusive.sample_index
        and right.audio_range.start.sample_index < left.audio_range.end_exclusive.sample_index
    )


def _choose_winner(left: _Candidate, right: _Candidate) -> tuple[_Candidate, _Candidate]:
    """Prefer confidence, then earlier chunk/start/end/id in a stable order."""

    if left.word.confidence != right.word.confidence:
        return (left, right) if left.word.confidence > right.word.confidence else (right, left)
    left_key = (
        left.chunk_index,
        left.word.audio_range.start.sample_index,
        left.word.audio_range.end_exclusive.sample_index,
        left.word.word_id,
        left.sequence,
    )
    right_key = (
        right.chunk_index,
        right.word.audio_range.start.sample_index,
        right.word.audio_range.end_exclusive.sample_index,
        right.word.word_id,
        right.sequence,
    )
    return (left, right) if left_key <= right_key else (right, left)


def _normalized_text(value: str) -> str:
    return normalize("NFC", value).casefold()


__all__ = [
    "DeterministicChunkMerger",
    "MergeCompatibilityError",
    "MergeWarning",
    "MergeWarningCode",
    "MergedTranscript",
]
