"""
Base abstract interface and data structures for AI Lip-Sync Synthesis adapters.
"""

from __future__ import annotations

import abc
from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier
from aidub.speech.runtime import RecognitionRuntime


class LipSyncQualityTier(StrEnum):
    PREVIEW_FAST = "preview_fast"      # Tier 1 (e.g. MuseTalk) for rapid NLE timeline preview
    CINEMA_QUALITY = "cinema_quality"  # Tier 2 (e.g. LatentSync) for final high-res delivery


class LipSyncOptions(ContractModel):
    """Configuration parameters for lip-sync synthesis adapter."""

    quality_tier: LipSyncQualityTier = LipSyncQualityTier.PREVIEW_FAST
    fps: float = Field(default=24.0, gt=0.0)
    device: str = Field(default="cuda", max_length=32)
    face_padding: int = Field(default=10, ge=0, le=50)
    feather_margin_px: int = Field(default=12, ge=0, le=64)
    color_match_mode: str = Field(default="histogram", max_length=32)  # "none", "histogram", "mean_std"
    poisson_blending: bool = True
    anti_flicker_alpha: float = Field(default=0.85, ge=0.0, le=1.0)


class LipSyncResult(ContractModel):
    """Output descriptor for synthesized lip-sync video track segment."""

    job_id: Identifier
    shot_id: Identifier
    output_video_path: str = Field(min_length=1)
    quality_tier: LipSyncQualityTier
    rendered_frames: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    color_matched: bool = True
    anti_flicker_applied: bool = True


class LipSyncEngine(abc.ABC):
    """Abstract interface for AI lip-sync adapters."""

    @abc.abstractmethod
    def synthesize_lip_sync(
        self,
        shot_id: str,
        source_video_path: str,
        target_audio_path: str,
        output_directory: str,
        options: LipSyncOptions | None = None,
        runtime: RecognitionRuntime | None = None,
    ) -> LipSyncResult:
        """Synthesize visual lip movement matching target audio track."""


__all__ = [
    "LipSyncEngine",
    "LipSyncOptions",
    "LipSyncQualityTier",
    "LipSyncResult",
]
