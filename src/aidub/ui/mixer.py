"""
Broadcast-grade audio mixer engine and channel strip state management.

Features (Master Spec Section 27):
  - Per-track Volume Fader (-60 dB to +12 dB with linear gain conversion)
  - Stereo Panning (-1.0 to +1.0)
  - Mute & Solo solo-logic group solver
  - Channel peak metering (-60 dBFS to +6 dBFS) & clip indicator
"""

from __future__ import annotations

from pydantic import Field

from aidub.contracts.base import ContractModel
from aidub.ui.timeline.model import TrackId


class ChannelStripState(ContractModel):
    """Runtime state of a single mixer channel strip."""

    track_id: TrackId
    volume_db: float = Field(default=0.0, ge=-60.0, le=12.0)
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    muted: bool = False
    solo: bool = False
    peak_l_dbfs: float = Field(default=-60.0, ge=-60.0, le=6.0)
    peak_r_dbfs: float = Field(default=-60.0, ge=-60.0, le=6.0)
    clipped: bool = False

    @property
    def linear_gain(self) -> float:
        """Convert volume dB to linear multiplier."""
        if self.volume_db <= -60.0:
            return 0.0
        return float(10.0 ** (self.volume_db / 20.0))


class AudioMixerEngine:
    """
    Manages 9-track studio audio mixer state and solo/mute routing logic.
    """

    def __init__(self) -> None:
        self._channels: dict[TrackId, ChannelStripState] = {
            t_id: ChannelStripState(track_id=t_id) for t_id in TrackId if t_id.value.startswith("A")
        }
        self._master_volume_db: float = 0.0

    def get_channel(self, track_id: TrackId) -> ChannelStripState | None:
        return self._channels.get(track_id)

    def set_volume(self, track_id: TrackId, volume_db: float) -> ChannelStripState:
        """Set track volume in dB."""
        ch = self._require(track_id)
        updated = ch.model_copy(update={"volume_db": max(-60.0, min(12.0, volume_db))})
        self._channels[track_id] = updated
        return updated

    def set_pan(self, track_id: TrackId, pan: float) -> ChannelStripState:
        """Set track panning (-1.0 to +1.0)."""
        ch = self._require(track_id)
        updated = ch.model_copy(update={"pan": max(-1.0, min(1.0, pan))})
        self._channels[track_id] = updated
        return updated

    def toggle_mute(self, track_id: TrackId) -> ChannelStripState:
        """Toggle track mute state."""
        ch = self._require(track_id)
        updated = ch.model_copy(update={"muted": not ch.muted})
        self._channels[track_id] = updated
        return updated

    def toggle_solo(self, track_id: TrackId) -> ChannelStripState:
        """Toggle track solo state."""
        ch = self._require(track_id)
        updated = ch.model_copy(update={"solo": not ch.solo})
        self._channels[track_id] = updated
        return updated

    def is_track_audible(self, track_id: TrackId) -> bool:
        """
        Determine if track is audible based on Mute and Solo group logic.

        If ANY track is soloed, ONLY soloed tracks are audible (unless muted).
        """
        ch = self._channels.get(track_id)
        if ch is None or ch.muted:
            return False

        any_soloed = any(c.solo for c in self._channels.values())
        if any_soloed:
            return ch.solo
        return True

    def update_meter(
        self, track_id: TrackId, peak_l_dbfs: float, peak_r_dbfs: float
    ) -> ChannelStripState:
        """Update channel peak meter level and clip indicators."""
        ch = self._require(track_id)
        clipped = ch.clipped or peak_l_dbfs > 0.0 or peak_r_dbfs > 0.0
        updated = ch.model_copy(
            update={
                "peak_l_dbfs": round(peak_l_dbfs, 1),
                "peak_r_dbfs": round(peak_r_dbfs, 1),
                "clipped": clipped,
            }
        )
        self._channels[track_id] = updated
        return updated

    def reset_clips(self) -> None:
        """Reset all channel clip indicators."""
        for t_id, ch in self._channels.items():
            self._channels[t_id] = ch.model_copy(update={"clipped": False})

    def _require(self, track_id: TrackId) -> ChannelStripState:
        ch = self._channels.get(track_id)
        if ch is None:
            raise KeyError(f"audio track {track_id.value!r} is not registered in mixer")
        return ch


__all__ = [
    "AudioMixerEngine",
    "ChannelStripState",
]
