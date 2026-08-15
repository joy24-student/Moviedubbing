"""Application-level durable transcript editing use case."""

from __future__ import annotations

from aidub.infrastructure.transcripts import TranscriptStore
from aidub.transcript import (
    Transcript,
    TranscriptCommand,
    TranscriptCommandService,
    TranscriptMutationResult,
)


class DurableTranscriptService:
    """Load, mutate, and atomically persist one source transcript aggregate."""

    def __init__(
        self,
        store: TranscriptStore,
        *,
        commands: TranscriptCommandService | None = None,
    ) -> None:
        self._store = store
        self._commands = commands or TranscriptCommandService()

    def create(self, transcript: Transcript) -> Transcript:
        """Create the initial revision-zero source transcript."""

        return self._store.create(transcript)

    def get(self, *, project_id: str, media_asset_id: str, language: str) -> Transcript | None:
        """Read the latest snapshot without acquiring a long-lived project lock."""

        return self._store.get(
            project_id=project_id,
            media_asset_id=media_asset_id,
            language=language,
        )

    def apply(
        self,
        *,
        project_id: str,
        media_asset_id: str,
        language: str,
        command: TranscriptCommand,
    ) -> TranscriptMutationResult:
        """Execute one pure command and publish it with durable CAS protection."""

        current = self._store.require(
            project_id=project_id,
            media_asset_id=media_asset_id,
            language=language,
        )
        result = self._commands.apply(current, command)
        return self._store.commit(result)


__all__ = ["DurableTranscriptService"]
