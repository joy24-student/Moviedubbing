"""
Video Transform & Keyframe Animation Interpolation Engine.

Provides 2D/3D video transforms (position X/Y, scale, rotation, crop, opacity)
and keyframe interpolation (Linear, Ease-In, Ease-Out, Bezier splines).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier


class KeyframeInterpolationMode(StrEnum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    BEZIER = "bezier"


class KeyframePoint(ContractModel):
    """Single keyframe point."""

    keyframe_id: Identifier
    time_ms: int = Field(ge=0)
    value: float
    mode: KeyframeInterpolationMode = KeyframeInterpolationMode.LINEAR


class VideoTransform(ContractModel):
    """2D/3D video spatial transform state."""

    pos_x: float = Field(default=0.0)
    pos_y: float = Field(default=0.0)
    scale_x: float = Field(default=1.0, gt=0.0)
    scale_y: float = Field(default=1.0, gt=0.0)
    rotation_deg: float = Field(default=0.0)
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class KeyframeInterpolator:
    """
    Interpolates animation values across keyframe points.
    """

    def interpolate(self, keyframes: Sequence[KeyframePoint], target_time_ms: int) -> float:
        """
        Interpolate scalar value at target_time_ms.
        """
        if not keyframes:
            return 0.0

        sorted_kfs = sorted(keyframes, key=lambda k: k.time_ms)
        if target_time_ms <= sorted_kfs[0].time_ms:
            return sorted_kfs[0].value
        if target_time_ms >= sorted_kfs[-1].time_ms:
            return sorted_kfs[-1].value

        for i in range(len(sorted_kfs) - 1):
            k1 = sorted_kfs[i]
            k2 = sorted_kfs[i + 1]
            if k1.time_ms <= target_time_ms <= k2.time_ms:
                t = (target_time_ms - k1.time_ms) / (k2.time_ms - k1.time_ms)
                if k1.mode == KeyframeInterpolationMode.EASE_IN:
                    t = t * t
                elif k1.mode == KeyframeInterpolationMode.EASE_OUT:
                    t = math.sin(t * math.pi / 2.0)
                return k1.value + t * (k2.value - k1.value)

        return sorted_kfs[-1].value


__all__ = [
    "KeyframeInterpolationMode",
    "KeyframeInterpolator",
    "KeyframePoint",
    "VideoTransform",
]
