"""
Multitrack Timeline data models and SceneGraph layout engine.

Track layout specification (Master Spec Section 27):
  - V1: Original Video
  - V2: Lip Overlay
  - A1: Source Dialogue
  - A2: Dub Dialogue
  - A3: Music
  - A4: Effects
  - A5: Ambience
  - S1: Source Subtitles
  - S2: Target Subtitles
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier


class TrackKind(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"


class TrackId(StrEnum):
    V1 = "V1"  # Original Video
    V2 = "V2"  # Lip Overlay
    A1 = "A1"  # Source Dialogue
    A2 = "A2"  # Dub Dialogue
    A3 = "A3"  # Music
    A4 = "A4"  # Effects
    A5 = "A5"  # Ambience
    S1 = "S1"  # Source Subtitles
    S2 = "S2"  # Target Subtitles


TRACK_KINDS: dict[TrackId, TrackKind] = {
    TrackId.V1: TrackKind.VIDEO,
    TrackId.V2: TrackKind.VIDEO,
    TrackId.A1: TrackKind.AUDIO,
    TrackId.A2: TrackKind.AUDIO,
    TrackId.A3: TrackKind.AUDIO,
    TrackId.A4: TrackKind.AUDIO,
    TrackId.A5: TrackKind.AUDIO,
    TrackId.S1: TrackKind.SUBTITLE,
    TrackId.S2: TrackKind.SUBTITLE,
}


class TimelineClip(ContractModel):
    """A single renderable clip/utterance block on the multitrack timeline."""

    clip_id: Identifier
    track_id: TrackId
    start_ms: int = Field(ge=0)
    duration_ms: int = Field(ge=1)
    label: str = Field(default="", max_length=256)
    utterance_id: str = Field(default="", max_length=128)
    color_hex: str = Field(default="#4A90E2", max_length=16)
    selected: bool = False
    locked: bool = False
    muted: bool = False

    @property
    def end_ms(self) -> int:
        return self.start_ms + self.duration_ms


class TimelineTrack(ContractModel):
    """A single track on the multitrack timeline containing clips."""

    track_id: TrackId
    display_name: str = Field(max_length=64)
    kind: TrackKind
    muted: bool = False
    solo: bool = False
    locked: bool = False
    height_px: int = Field(default=48, ge=24, le=200)
    clips: list[TimelineClip] = Field(default_factory=list)


class TimelineLayoutEngine:
    """
    High-performance 60 FPS SceneGraph layout calculation engine.

    Maps (track, time_ms) coordinates to screen (x_px, y_px, width_px, height_px)
    viewport pixels for rendering 100,000+ clips smoothly.
    """

    def __init__(
        self,
        zoom_px_per_sec: float = 100.0,
        viewport_width_px: int = 1920,
        viewport_height_px: int = 1080,
    ) -> None:
        self.zoom_px_per_sec = max(1.0, min(5000.0, zoom_px_per_sec))
        self.viewport_width_px = viewport_width_px
        self.viewport_height_px = viewport_height_px
        self.scroll_x_ms: int = 0
        self.scroll_y_px: int = 0

    def time_to_px(self, time_ms: int) -> float:
        """Convert timeline time in ms to pixel x-offset."""
        return (time_ms - self.scroll_x_ms) * (self.zoom_px_per_sec / 1000.0)

    def px_to_time(self, px: float) -> int:
        """Convert pixel x-offset to timeline time in ms."""
        return int(self.scroll_x_ms + (px / (self.zoom_px_per_sec / 1000.0)))

    def visible_clips(
        self,
        tracks: list[TimelineTrack],
    ) -> list[tuple[TimelineClip, float, float, float, float]]:
        """
        Compute pixel bounding boxes (x, y, width, height) for all visible clips.
        Clips outside the viewport bounds are culled.
        """
        visible: list[tuple[TimelineClip, float, float, float, float]] = []
        visible_start_ms = self.scroll_x_ms
        visible_end_ms = self.px_to_time(self.viewport_width_px)

        curr_y = -self.scroll_y_px
        for track in tracks:
            track_h = track.height_px
            if curr_y + track_h >= 0 and curr_y <= self.viewport_height_px:
                for clip in track.clips:
                    if clip.end_ms >= visible_start_ms and clip.start_ms <= visible_end_ms:
                        x = self.time_to_px(clip.start_ms)
                        w = max(2.0, clip.duration_ms * (self.zoom_px_per_sec / 1000.0))
                        visible.append((clip, x, float(curr_y), w, float(track_h)))
            curr_y += track_h

        return visible


def create_default_multitrack_timeline() -> list[TimelineTrack]:
    """Factory creating standard 9-track layout per Master Spec Section 27."""
    names = {
        TrackId.V1: "V1: Original Video",
        TrackId.V2: "V2: Lip Overlay",
        TrackId.A1: "A1: Source Dialogue",
        TrackId.A2: "A2: Dub Dialogue",
        TrackId.A3: "A3: Music",
        TrackId.A4: "A4: Effects",
        TrackId.A5: "A5: Ambience",
        TrackId.S1: "S1: Source Subtitles",
        TrackId.S2: "S2: Target Subtitles",
    }
    return [
        TimelineTrack(
            track_id=t_id,
            display_name=names[t_id],
            kind=TRACK_KINDS[t_id],
        )
        for t_id in TrackId
    ]


__all__ = [
    "TRACK_KINDS",
    "TimelineClip",
    "TimelineLayoutEngine",
    "TimelineTrack",
    "TrackId",
    "TrackKind",
    "create_default_multitrack_timeline",
]
