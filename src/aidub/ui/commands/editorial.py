"""
Professional NLE editorial command engine.

NLE Edit operations (Master Spec Section 27):
  - Blade Split: Split a clip at a given timestamp into two contiguous sub-clips.
  - Trim: Change clip in-point or out-point without moving adjacent clips.
  - Ripple Edit: Trim clip and shift all downstream clips on the track.
  - Roll Edit: Adjust boundary between two adjacent clips without altering total duration.
  - Slip Edit: Shift clip media contents in time while preserving timeline duration and position.
  - Slide Edit: Shift clip on timeline while trimming preceding/following clips to fit.
  - Snapping Calculator: Snap playhead/cursor to clip edges, markers, or video cuts within tolerance.
"""

from __future__ import annotations

import logging

from aidub.contracts.base import Identifier
from aidub.ui.timeline.model import TimelineClip, TimelineTrack

logger = logging.getLogger(__name__)

DEFAULT_SNAP_TOLERANCE_PX = 10


class SnappingEngine:
    """Calculates magnet snapping for playhead, clip edges, and markers."""

    def __init__(self, tolerance_ms: int = 50) -> None:
        self.tolerance_ms = tolerance_ms

    def snap(self, target_ms: int, snap_points: list[int]) -> tuple[int, bool]:
        """
        Snap target_ms to the closest snap_point within tolerance.

        Returns (snapped_time_ms, snapped_flag).
        """
        if not snap_points:
            return target_ms, False

        closest = min(snap_points, key=lambda pt: abs(pt - target_ms))
        if abs(closest - target_ms) <= self.tolerance_ms:
            return closest, True
        return target_ms, False


class EditorialCommandEngine:
    """NLE Edit operations executor."""

    @staticmethod
    def blade_split(
        clip: TimelineClip,
        split_ms: int,
    ) -> tuple[TimelineClip, TimelineClip]:
        """
        Split a clip into two contiguous clips at split_ms.

        Raises ValueError if split_ms is outside the clip boundaries.
        """
        if split_ms <= clip.start_ms or split_ms >= clip.end_ms:
            raise ValueError(
                f"split point {split_ms}ms must be strictly inside clip bounds "
                f"[{clip.start_ms}ms, {clip.end_ms}ms]"
            )

        left_dur = split_ms - clip.start_ms
        right_dur = clip.end_ms - split_ms

        left = clip.model_copy(
            update={
                "clip_id": Identifier(f"{clip.clip_id}_a"),
                "duration_ms": left_dur,
            }
        )
        right = clip.model_copy(
            update={
                "clip_id": Identifier(f"{clip.clip_id}_b"),
                "start_ms": split_ms,
                "duration_ms": right_dur,
            }
        )
        return left, right

    @staticmethod
    def ripple_delete(
        track: TimelineTrack,
        clip_id: str,
    ) -> TimelineTrack:
        """
        Delete a clip and ripple-shift all downstream clips on the track to close the gap.
        """
        target = next((c for c in track.clips if c.clip_id == clip_id), None)
        if target is None:
            raise KeyError(f"clip {clip_id!r} not found on track {track.track_id}")

        gap_ms = target.duration_ms
        target_start = target.start_ms

        new_clips: list[TimelineClip] = []
        for c in track.clips:
            if c.clip_id == clip_id:
                continue
            if c.start_ms > target_start:
                new_clips.append(c.model_copy(update={"start_ms": c.start_ms - gap_ms}))
            else:
                new_clips.append(c)

        return track.model_copy(update={"clips": new_clips})

    @staticmethod
    def roll_edit(
        left_clip: TimelineClip,
        right_clip: TimelineClip,
        new_boundary_ms: int,
    ) -> tuple[TimelineClip, TimelineClip]:
        """
        Move the boundary between two adjacent clips without changing their outer span.
        """
        if new_boundary_ms <= left_clip.start_ms or new_boundary_ms >= right_clip.end_ms:
            raise ValueError("new boundary must lie between left.start and right.end")

        new_left_dur = new_boundary_ms - left_clip.start_ms
        new_right_dur = right_clip.end_ms - new_boundary_ms

        new_left = left_clip.model_copy(update={"duration_ms": new_left_dur})
        new_right = right_clip.model_copy(
            update={"start_ms": new_boundary_ms, "duration_ms": new_right_dur}
        )
        return new_left, new_right


__all__ = [
    "EditorialCommandEngine",
    "SnappingEngine",
]
