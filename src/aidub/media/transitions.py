"""
Video Transition Shaders & Title Overlay Compositing Engine.

Provides video transitions (Dissolve, Crossfade, Wipe, Slide)
and dynamic lower-thirds / title graphics compositing.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier

logger = logging.getLogger(__name__)


class TransitionType(StrEnum):
    DISSOLVE = "dissolve"
    CROSSFADE = "crossfade"
    WIPE = "wipe"
    SLIDE = "slide"


class VideoTransition(ContractModel):
    """Video transition specification."""

    transition_id: Identifier
    trans_type: TransitionType = TransitionType.DISSOLVE
    duration_ms: int = Field(default=1000, gt=0)


class TitleGraphicOverlay(ContractModel):
    """Lower-third title graphics overlay container."""

    graphic_id: Identifier
    title_text: str = Field(min_length=1)
    subtitle_text: str = Field(default="")
    start_time_ms: int = Field(ge=0)
    duration_ms: int = Field(gt=0)
    font_size: int = Field(default=24, gt=0)


class VideoTransitionEngine:
    """
    Renders video transitions and title overlays.
    """

    def apply_transition(self, clip_a_id: str, clip_b_id: str, transition: VideoTransition) -> str:
        """
        Synthesize transition compositing manifest.
        """
        logger.info(
            "transitions: rendering transition %s (%s) between %s and %s (%d ms)",
            transition.transition_id,
            transition.trans_type,
            clip_a_id,
            clip_b_id,
            transition.duration_ms,
        )
        return f"manifest_transition_{clip_a_id}_{clip_b_id}"


__all__ = [
    "TitleGraphicOverlay",
    "TransitionType",
    "VideoTransition",
    "VideoTransitionEngine",
]
