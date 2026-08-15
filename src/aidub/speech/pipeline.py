"""Long-form orchestration over the engine-neutral recognition boundary."""

from __future__ import annotations

from .chunking import ChunkingPolicy, DeterministicChunkPlanner, PlannedAudioChunk
from .contracts import (
    RecognitionPhase,
    RecognitionProgress,
    RecognitionProvenance,
    SpeechRecognitionRequest,
)
from .merge import DeterministicChunkMerger, MergedTranscript
from .recognizer import SpeechRecognizer
from .runtime import NullRecognitionRuntime, RecognitionRuntime


class RecognitionBoundaryError(ValueError):
    """Raised when an adapter returns output that does not match its request."""


class LongFormTranscriber:
    """Plan, recognize, validate, and merge a complete source range."""

    def __init__(
        self,
        recognizer: SpeechRecognizer,
        *,
        planner: DeterministicChunkPlanner | None = None,
        merger: DeterministicChunkMerger | None = None,
    ) -> None:
        self._recognizer = recognizer
        self._planner = planner or DeterministicChunkPlanner()
        self._merger = merger or DeterministicChunkMerger()

    def transcribe(
        self,
        request: SpeechRecognitionRequest,
        policy: ChunkingPolicy,
        *,
        runtime: RecognitionRuntime | None = None,
    ) -> MergedTranscript:
        """Transcribe a full-range template through deterministic chunk requests."""

        if request.audio_range != request.full_audio_range:
            raise RecognitionBoundaryError(
                "long-form request template must cover its complete audio range"
            )
        if request.chunk_index != 0 or request.chunk_count != 1:
            raise RecognitionBoundaryError(
                "long-form request template must use chunk index zero and chunk count one"
            )

        active_runtime = runtime if runtime is not None else NullRecognitionRuntime()
        active_runtime.checkpoint()
        plan = self._planner.plan(request.full_audio_range, policy)
        total_samples = plan.source_range.sample_count
        chunk_count = len(plan.chunks)
        self._report(
            active_runtime,
            request=request,
            phase=RecognitionPhase.PLANNING,
            completed_samples=0,
            total_samples=total_samples,
            chunk_index=None,
            chunk_count=chunk_count,
        )

        identity = self._recognizer.identity
        results = []
        completed_samples = 0
        for chunk in plan.chunks:
            active_runtime.checkpoint()
            chunk_request = _request_for_chunk(request, chunk, chunk_count)
            self._report(
                active_runtime,
                request=request,
                phase=RecognitionPhase.RECOGNIZING,
                completed_samples=completed_samples,
                total_samples=total_samples,
                chunk_index=chunk.index,
                chunk_count=chunk_count,
            )
            result = self._recognizer.recognize(chunk_request, runtime=active_runtime)
            active_runtime.checkpoint()
            expected = RecognitionProvenance.from_request(chunk_request, identity)
            if result.provenance != expected:
                raise RecognitionBoundaryError(
                    f"recognizer result provenance does not match chunk {chunk.index} request"
                )
            results.append(result)
            completed_samples = (
                chunk.audio_range.end_exclusive.sample_index - plan.source_range.start.sample_index
            )
            self._report(
                active_runtime,
                request=request,
                phase=RecognitionPhase.RECOGNIZING,
                completed_samples=completed_samples,
                total_samples=total_samples,
                chunk_index=chunk.index,
                chunk_count=chunk_count,
            )

        active_runtime.checkpoint()
        self._report(
            active_runtime,
            request=request,
            phase=RecognitionPhase.MERGING,
            completed_samples=total_samples,
            total_samples=total_samples,
            chunk_index=None,
            chunk_count=chunk_count,
        )
        merged = self._merger.merge(plan, tuple(results))
        active_runtime.checkpoint()
        self._report(
            active_runtime,
            request=request,
            phase=RecognitionPhase.COMPLETE,
            completed_samples=total_samples,
            total_samples=total_samples,
            chunk_index=None,
            chunk_count=chunk_count,
        )
        return merged

    @staticmethod
    def _report(
        runtime: RecognitionRuntime,
        *,
        request: SpeechRecognitionRequest,
        phase: RecognitionPhase,
        completed_samples: int,
        total_samples: int,
        chunk_index: int | None,
        chunk_count: int,
    ) -> None:
        runtime.report(
            RecognitionProgress(
                request_id=request.request_id,
                phase=phase,
                completed_samples=completed_samples,
                total_samples=total_samples,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            )
        )


def _request_for_chunk(
    template: SpeechRecognitionRequest,
    chunk: PlannedAudioChunk,
    chunk_count: int,
) -> SpeechRecognitionRequest:
    return SpeechRecognitionRequest(
        request_id=template.request_id,
        project_id=template.project_id,
        media_asset_id=template.media_asset_id,
        source_audio_sha256=template.source_audio_sha256,
        language=template.language,
        full_audio_range=template.full_audio_range,
        audio_range=chunk.audio_range,
        channel_index=template.channel_index,
        chunk_index=chunk.index,
        chunk_count=chunk_count,
    )


__all__ = ["LongFormTranscriber", "RecognitionBoundaryError"]
