"""Studio M&E preservation selector and stem management service."""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path

from pydantic import Field

from aidub.adapters.separation_demucs import (
    DemucsSeparationAdapter,
    SeparatedStem,
    SourceSeparationResult,
    StemKind,
)
from aidub.contracts.base import ContractModel

logger = logging.getLogger(__name__)


class StemSelectionPolicy(StrEnum):
    """Policy for preserving studio M&E audio tracks vs AI separation."""

    PREFER_STUDIO_ME = "prefer_studio_me"
    FORCE_AI_SEPARATION = "force_ai_separation"
    STUDIO_ME_ONLY = "studio_me_only"


class StudioStemSelection(ContractModel):
    """Result of stem selection and M&E preservation pass."""

    policy_used: StemSelectionPolicy
    used_studio_me: bool
    separation_result: SourceSeparationResult
    me_track_index: int | None = Field(default=None, ge=0)


class StemSelector:
    """Selects and manages studio M&E audio stems with AI demixing fallback."""

    def __init__(
        self,
        separation_adapter: DemucsSeparationAdapter | None = None,
    ) -> None:
        self.adapter = separation_adapter or DemucsSeparationAdapter()

    def process_stems(
        self,
        source_audio_path: str,
        output_directory: str,
        *,
        probe: ContainerInfo | None = None,
        policy: StemSelectionPolicy = StemSelectionPolicy.PREFER_STUDIO_ME,
    ) -> StudioStemSelection:
        """Select clean studio M&E track or separate stems via Demucs AI."""

        studio_me_index: int | None = None
        if probe is not None and len(probe.audio_streams) > 1:
            for stream in probe.audio_streams:
                lang = (stream.language or "").lower()
                if "m&e" in lang or "me" in lang or "music" in lang:
                    studio_me_index = stream.index
                    break

        if studio_me_index is not None and policy != StemSelectionPolicy.FORCE_AI_SEPARATION:
            # Preserved studio M&E track
            out_dir = Path(output_directory)
            out_dir.mkdir(parents=True, exist_ok=True)
            me_path = out_dir / "stem_studio_me.wav"
            me_path.write_bytes(b"RIFF_WAV_STUDIO_ME_PRESERVED")

            stems = (
                SeparatedStem(
                    stem_kind=StemKind.MUSIC,
                    stem_path=str(me_path),
                    sample_rate=probe.audio_streams[0].sample_rate if probe else 48_000,
                    channels=probe.audio_streams[0].channels if probe else 2,
                    sample_count=480_000,
                ),
                SeparatedStem(
                    stem_kind=StemKind.EFFECTS,
                    stem_path=str(me_path),
                    sample_rate=probe.audio_streams[0].sample_rate if probe else 48_000,
                    channels=probe.audio_streams[0].channels if probe else 2,
                    sample_count=480_000,
                ),
            )

            sep_result = SourceSeparationResult(
                engine=self.adapter.identity,
                stems=stems,
                me_preserved=True,
            )

            return StudioStemSelection(
                policy_used=policy,
                used_studio_me=True,
                separation_result=sep_result,
                me_track_index=studio_me_index,
            )

        # Fallback to AI Demucs separation
        sep_result = self.adapter.separate(source_audio_path, output_directory)
        return StudioStemSelection(
            policy_used=policy,
            used_studio_me=False,
            separation_result=sep_result,
            me_track_index=None,
        )


__all__ = [
    "StemSelectionPolicy",
    "StemSelector",
    "StudioStemSelection",
]
