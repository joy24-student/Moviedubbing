"""Cooperative local cancellation and progress callbacks for analysis adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from .models import AnalysisCancellation, AnalysisProgress


class SourceAnalysisCancelledError(RuntimeError):
    """Raised by a cooperative checkpoint with the structured cancellation fact."""

    def __init__(self, cancellation: AnalysisCancellation) -> None:
        super().__init__(f"source analysis cancelled: {cancellation.reason}")
        self.cancellation = cancellation


@runtime_checkable
class SourceAnalysisRuntime(Protocol):
    """Small runtime seam shared by every local source-analysis adapter."""

    def checkpoint(self) -> None:
        """Raise ``SourceAnalysisCancelledError`` when work must stop."""

    def report(self, progress: AnalysisProgress) -> None:
        """Publish one fully validated, monotonic progress snapshot."""


class NullSourceAnalysisRuntime:
    """Default runtime for synchronous local callers that require no callbacks."""

    def checkpoint(self) -> None:
        return

    def report(self, progress: AnalysisProgress) -> None:
        del progress


class CallbackSourceAnalysisRuntime:
    """Adapt local cancellation and progress callbacks without introducing a queue SDK."""

    def __init__(
        self,
        *,
        cancellation: Callable[[], AnalysisCancellation | None],
        on_progress: Callable[[AnalysisProgress], None],
    ) -> None:
        self._cancellation = cancellation
        self._on_progress = on_progress

    def checkpoint(self) -> None:
        cancellation = self._cancellation()
        if cancellation is not None:
            raise SourceAnalysisCancelledError(cancellation)

    def report(self, progress: AnalysisProgress) -> None:
        self._on_progress(progress)


__all__ = [
    "CallbackSourceAnalysisRuntime",
    "NullSourceAnalysisRuntime",
    "SourceAnalysisCancelledError",
    "SourceAnalysisRuntime",
]
