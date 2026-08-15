"""Engine adapters for AI models, media runtimes, and external providers."""

from .asr_whisper import FasterWhisperAdapter, FasterWhisperOptions
from .diarization_pyannote import (
    DiarizedSpeakerSegment,
    PyannoteDiarizationAdapter,
    PyannoteDiarizationOptions,
    SpeakerDiarizationResult,
    cluster_speaker_embeddings,
)
from .separation_demucs import (
    DemucsSeparationAdapter,
    DemucsSeparationOptions,
    SeparatedStem,
    SourceSeparationResult,
    StemKind,
)

__all__ = [
    "DemucsSeparationAdapter",
    "DemucsSeparationOptions",
    "DiarizedSpeakerSegment",
    "FasterWhisperAdapter",
    "FasterWhisperOptions",
    "PyannoteDiarizationAdapter",
    "PyannoteDiarizationOptions",
    "SeparatedStem",
    "SourceSeparationResult",
    "SpeakerDiarizationResult",
    "StemKind",
    "cluster_speaker_embeddings",
]
