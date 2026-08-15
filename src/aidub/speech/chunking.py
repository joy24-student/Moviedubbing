"""Deterministic integer-sample planning for long-form recognition."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from aidub.domain.time import AudioSamplePosition, AudioSampleRange

from .contracts import SpeechContractModel


class ChunkPlanningError(ValueError):
    """Raised when a source range cannot satisfy the configured hard bounds."""


class ChunkingPolicy(SpeechContractModel):
    """Hard chunk limits expressed only in integer samples."""

    sample_rate: int = Field(gt=0, le=768_000)
    max_chunk_samples: int = Field(gt=0)
    min_chunk_samples: int = Field(gt=0)
    overlap_samples: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_bounds(self) -> Self:
        if self.min_chunk_samples > self.max_chunk_samples:
            raise ValueError("minimum chunk size cannot exceed maximum chunk size")
        if self.overlap_samples >= self.min_chunk_samples:
            raise ValueError("overlap must be smaller than the minimum chunk size")
        return self


class PlannedAudioChunk(SpeechContractModel):
    index: int = Field(ge=0)
    audio_range: AudioSampleRange
    left_overlap_samples: int = Field(ge=0)
    right_overlap_samples: int = Field(ge=0)


class AudioChunkPlan(SpeechContractModel):
    source_range: AudioSampleRange
    policy: ChunkingPolicy
    chunks: tuple[PlannedAudioChunk, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_plan(self) -> Self:
        if self.source_range.sample_rate != self.policy.sample_rate:
            raise ValueError("chunk plan source and policy use different sample rates")
        if self.chunks[0].audio_range.start != self.source_range.start:
            raise ValueError("first chunk must start at the source-range start")
        if self.chunks[-1].audio_range.end_exclusive != self.source_range.end_exclusive:
            raise ValueError("last chunk must end at the source-range end")

        for index, chunk in enumerate(self.chunks):
            if chunk.index != index:
                raise ValueError("chunk indices must be contiguous and zero based")
            if chunk.audio_range.sample_rate != self.policy.sample_rate:
                raise ValueError("planned chunks must use the policy sample rate")
            if chunk.audio_range.sample_count > self.policy.max_chunk_samples:
                raise ValueError("planned chunk exceeds maximum size")
            if (
                len(self.chunks) > 1
                and chunk.audio_range.sample_count < self.policy.min_chunk_samples
            ):
                raise ValueError("planned chunk is below minimum size")
            expected_left = 0 if index == 0 else self.policy.overlap_samples
            expected_right = 0 if index == len(self.chunks) - 1 else self.policy.overlap_samples
            if chunk.left_overlap_samples != expected_left:
                raise ValueError("planned chunk has an invalid left overlap")
            if chunk.right_overlap_samples != expected_right:
                raise ValueError("planned chunk has an invalid right overlap")
            if index > 0:
                previous = self.chunks[index - 1]
                actual_overlap = (
                    previous.audio_range.end_exclusive.sample_index
                    - chunk.audio_range.start.sample_index
                )
                if actual_overlap != self.policy.overlap_samples:
                    raise ValueError("adjacent chunks must use the configured overlap")
        return self


class DeterministicChunkPlanner:
    """Balance chunks exactly while preserving a fixed adjacent overlap."""

    def plan(self, source_range: AudioSampleRange, policy: ChunkingPolicy) -> AudioChunkPlan:
        if source_range.is_empty:
            raise ChunkPlanningError("cannot plan an empty audio range")
        if source_range.sample_rate != policy.sample_rate:
            raise ChunkPlanningError("source range and chunking policy use different sample rates")

        sample_count = source_range.sample_count
        if sample_count <= policy.max_chunk_samples:
            return AudioChunkPlan(
                source_range=source_range,
                policy=policy,
                chunks=(
                    PlannedAudioChunk(
                        index=0,
                        audio_range=source_range,
                        left_overlap_samples=0,
                        right_overlap_samples=0,
                    ),
                ),
            )

        effective_capacity = policy.max_chunk_samples - policy.overlap_samples
        chunk_count = _ceil_div(
            sample_count - policy.overlap_samples,
            effective_capacity,
        )
        total_chunk_samples = sample_count + (chunk_count - 1) * policy.overlap_samples
        base_size, larger_chunk_count = divmod(total_chunk_samples, chunk_count)
        if base_size < policy.min_chunk_samples:
            raise ChunkPlanningError(
                "source range cannot satisfy minimum size with the configured maximum and overlap"
            )

        chunks: list[PlannedAudioChunk] = []
        start_index = source_range.start.sample_index
        for index in range(chunk_count):
            chunk_size = base_size + (1 if index < larger_chunk_count else 0)
            chunk_range = AudioSampleRange(
                start=AudioSamplePosition(
                    sample_index=start_index,
                    sample_rate=policy.sample_rate,
                ),
                sample_count=chunk_size,
            )
            chunks.append(
                PlannedAudioChunk(
                    index=index,
                    audio_range=chunk_range,
                    left_overlap_samples=0 if index == 0 else policy.overlap_samples,
                    right_overlap_samples=(
                        0 if index == chunk_count - 1 else policy.overlap_samples
                    ),
                )
            )
            start_index += chunk_size - policy.overlap_samples

        return AudioChunkPlan(
            source_range=source_range,
            policy=policy,
            chunks=tuple(chunks),
        )


def _ceil_div(numerator: int, denominator: int) -> int:
    return -(-numerator // denominator)


__all__ = [
    "AudioChunkPlan",
    "ChunkPlanningError",
    "ChunkingPolicy",
    "DeterministicChunkPlanner",
    "PlannedAudioChunk",
]
