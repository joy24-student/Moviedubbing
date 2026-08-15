"""
Fast subtitle burn-in overlay generator & SDH caption tag injector.

Features:
  - FFmpeg Subtitle Burn-in: Builds hardware-accelerated subtitle overlay filter strings.
  - SDH Captions: Injects speaker color tags and sound effect descriptors ([GUNSHOT], [LAUGHTER]).
"""

from __future__ import annotations

import logging
from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel
from aidub.subtitles.qc import SubtitleCue

logger = logging.getLogger(__name__)


class SdhSoundEffect(StrEnum):
    GUNSHOT = "[GUNSHOT]"
    EXPLOSION = "[EXPLOSION]"
    LAUGHTER = "[LAUGHTER]"
    APPLAUSE = "[APPLAUSE]"
    MUSIC_PLAYING = "[MUSIC PLAYING]"
    THUNDER = "[THUNDER]"
    DOOR_CREAKS = "[DOOR CREAKS]"


class SubtitleBurnInConfig(ContractModel):
    """Configuration for hardware-accelerated subtitle video burn-in."""

    ass_file_path: str = Field(min_length=1)
    font_name: str = Field(default="Segoe UI", max_length=64)
    font_size: int = Field(default=24, ge=12, le=72)
    primary_color_hex: str = Field(default="&H00FFFFFF", max_length=16)
    outline_color_hex: str = Field(default="&H00000000", max_length=16)
    outline_width: int = Field(default=2, ge=0, le=10)
    shadow_depth: int = Field(default=2, ge=0, le=10)
    use_gpu: bool = True


class SdhCaptionInjector:
    """
    Injects SDH sound effect tags and speaker color identifiers into subtitle cues.
    """

    @staticmethod
    def inject_sound_effect(cue: SubtitleCue, effect: SdhSoundEffect) -> SubtitleCue:
        """Prepend an SDH sound effect descriptor tag to a cue."""
        new_text = f"{effect.value} {cue.text.strip()}"
        return cue.model_copy(update={"text": new_text})

    @staticmethod
    def inject_speaker_label(cue: SubtitleCue, speaker_name: str) -> SubtitleCue:
        """Prepend a speaker name identifier (e.g. 'TONY: Hello') to a cue."""
        new_text = f"{speaker_name.upper()}: {cue.text.strip()}"
        return cue.model_copy(update={"text": new_text})


class SubtitleBurnInEngine:
    """
    Generates hardware-accelerated FFmpeg video filter strings for subtitle burn-in.
    """

    @staticmethod
    def build_ffmpeg_burnin_filter(config: SubtitleBurnInConfig) -> str:
        """
        Build FFmpeg vf subtitle burn-in filter complex argument.
        Escapes Windows backslashes for FFmpeg syntax compatibility.
        """
        escaped_path = config.ass_file_path.replace("\\", "/").replace(":", "\\:")
        filter_str = f"subtitles=filename='{escaped_path}'"

        style_override = (
            f":force_style='Fontname={config.font_name},"
            f"Fontsize={config.font_size},"
            f"PrimaryColour={config.primary_color_hex},"
            f"OutlineColour={config.outline_color_hex},"
            f"Outline={config.outline_width},"
            f"Shadow={config.shadow_depth}'"
        )
        return filter_str + style_override


__all__ = [
    "SdhCaptionInjector",
    "SdhSoundEffect",
    "SubtitleBurnInConfig",
    "SubtitleBurnInEngine",
]
