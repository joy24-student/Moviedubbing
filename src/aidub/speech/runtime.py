"""Cooperative cancellation and progress adapters for recognizer engines."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from .contracts import RecognitionProgress


class RecognitionCancelledError(RuntimeError):
    """Raised at a cooperative checkpoint after cancellation is requested."""


@runtime_checkable
class RecognitionRuntime(Protocol):
    """Minimal runtime seam exposed to model adapters."""

    def checkpoint(self) -> None:
        """Raise when cancellation has been requested."""

    def report(self, progress: RecognitionProgress) -> None:
        """Publish validated progress without prescribing a UI or queue."""


class NullRecognitionRuntime:
    """Runtime used by synchronous callers that need no callbacks."""

    def checkpoint(self) -> None:
        return

    def report(self, progress: RecognitionProgress) -> None:
        del progress


class CallbackRecognitionRuntime:
    """Adapt plain cancellation/progress callbacks to ``RecognitionRuntime``."""

    def __init__(
        self,
        *,
        is_cancelled: Callable[[], bool],
        on_progress: Callable[[RecognitionProgress], None],
    ) -> None:
        self._is_cancelled = is_cancelled
        self._on_progress = on_progress

    def checkpoint(self) -> None:
        if self._is_cancelled():
            raise RecognitionCancelledError("speech recognition was cancelled")

    def report(self, progress: RecognitionProgress) -> None:
        self._on_progress(progress)


__all__ = [
    "CallbackRecognitionRuntime",
    "NullRecognitionRuntime",
    "RecognitionCancelledError",
    "RecognitionRuntime",
]
