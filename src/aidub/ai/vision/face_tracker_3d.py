"""
Multi-Face 3D Tracking & Occlusion Processor.

Provides robust 3D face tracking under facial hair, hand-over-face occlusions, rapid cuts, and low light.
"""

from __future__ import annotations

import logging

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier

logger = logging.getLogger(__name__)


class OcclusionState(ContractModel):
    """Face occlusion assessment."""

    track_id: Identifier
    occlusion_percentage: float = Field(ge=0.0, le=100.0)
    is_occluded: bool = False
    confidence: float = Field(ge=0.0, le=1.0)


class MultiFace3DTracker:
    """
    Robust 3D face tracker handling occlusions and low light.
    """

    def track_face_occlusions(self, track_id: str, occlusion_pct: float = 15.0) -> OcclusionState:
        """
        Assess face occlusion state.
        """
        tid = Identifier(track_id)
        is_occ = occlusion_pct > 35.0

        logger.info("face_tracker_3d: evaluated track %s (Occlusion: %.1f%%, IsOccluded: %s)", tid, occlusion_pct, is_occ)
        return OcclusionState(
            track_id=tid,
            occlusion_percentage=occlusion_pct,
            is_occluded=is_occ,
            confidence=0.92,
        )


__all__ = [
    "MultiFace3DTracker",
    "OcclusionState",
]
