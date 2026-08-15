"""The engine-neutral local speech-recognizer protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contracts import RecognitionChunkResult, SpeechEngineIdentity, SpeechRecognitionRequest
from .runtime import RecognitionRuntime


@runtime_checkable
class SpeechRecognizer(Protocol):
    """Implemented by local ASR adapters without coupling the core to a model SDK."""

    @property
    def identity(self) -> SpeechEngineIdentity:
        """Return the executable/model identity used for every emitted token."""

    def recognize(
        self,
        request: SpeechRecognitionRequest,
        *,
        runtime: RecognitionRuntime,
    ) -> RecognitionChunkResult:
        """Recognize one exact source-audio chunk cooperatively."""


__all__ = ["SpeechRecognizer"]
