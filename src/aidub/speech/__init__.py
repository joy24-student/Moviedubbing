"""Local, deterministic speech-recognition boundary and long-form pipeline."""

from .chunking import (
    AudioChunkPlan,
    ChunkingPolicy,
    ChunkPlanningError,
    DeterministicChunkPlanner,
    PlannedAudioChunk,
)
from .contracts import (
    RecognitionChunkResult,
    RecognitionPhase,
    RecognitionProgress,
    RecognitionProvenance,
    RecognitionWarning,
    RecognizedSegment,
    RecognizedWord,
    SpeechEngineIdentity,
    SpeechRecognitionRequest,
)
from .merge import (
    DeterministicChunkMerger,
    MergeCompatibilityError,
    MergedTranscript,
    MergeWarning,
    MergeWarningCode,
)
from .pipeline import LongFormTranscriber, RecognitionBoundaryError
from .recognizer import SpeechRecognizer
from .runtime import (
    CallbackRecognitionRuntime,
    NullRecognitionRuntime,
    RecognitionCancelledError,
    RecognitionRuntime,
)

__all__ = [
    "AudioChunkPlan",
    "CallbackRecognitionRuntime",
    "ChunkPlanningError",
    "ChunkingPolicy",
    "DeterministicChunkMerger",
    "DeterministicChunkPlanner",
    "LongFormTranscriber",
    "MergeCompatibilityError",
    "MergeWarning",
    "MergeWarningCode",
    "MergedTranscript",
    "NullRecognitionRuntime",
    "PlannedAudioChunk",
    "RecognitionBoundaryError",
    "RecognitionCancelledError",
    "RecognitionChunkResult",
    "RecognitionPhase",
    "RecognitionProgress",
    "RecognitionProvenance",
    "RecognitionRuntime",
    "RecognitionWarning",
    "RecognizedSegment",
    "RecognizedWord",
    "SpeechEngineIdentity",
    "SpeechRecognitionRequest",
    "SpeechRecognizer",
]
