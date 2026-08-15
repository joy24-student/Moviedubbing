"""Provider-neutral protocol for local source-analysis adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import AnalysisRun, LocalAnalyzerIdentity, SourceAnalysisRequest
from .runtime import SourceAnalysisRuntime


@runtime_checkable
class LocalSourceAnalysisProvider(Protocol):
    """A local adapter that executes a fixed analysis request cooperatively.

    Implementations may wrap FFmpeg, an approved local model, or deterministic
    rules.  They must not expose a provider-specific object graph through this
    public contract.
    """

    @property
    def identity(self) -> LocalAnalyzerIdentity:
        """Return the installed adapter/engine/model identity used for this run."""

    def analyze(
        self,
        request: SourceAnalysisRequest,
        *,
        runtime: SourceAnalysisRuntime,
    ) -> AnalysisRun:
        """Return a complete immutable run snapshot or raise a structured boundary error."""


__all__ = ["LocalSourceAnalysisProvider"]
