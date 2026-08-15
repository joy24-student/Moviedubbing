"""
Timeline markers & In/Out range selection engine.

Features (Master Spec Section 27):
  - Mark In ('I') & Mark Out ('O') range selection for selective rendering / export
  - Timeline markers (Scene, Chapter, QC Flag, Comment) with color coding
  - Magnet snapping to markers
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier


class MarkerKind(StrEnum):
    SCENE_CUT = "scene_cut"
    CHAPTER = "chapter"
    QC_FLAG = "qc_flag"
    COMMENT = "comment"


class TimelineMarker(ContractModel):
    """A single timeline marker indicator."""

    marker_id: Identifier
    position_ms: int = Field(ge=0)
    kind: MarkerKind = MarkerKind.COMMENT
    label: str = Field(default="", max_length=256)
    color_hex: str = Field(default="#6366F1", max_length=16)


class InOutRange(ContractModel):
    """Active Mark In ('I') / Mark Out ('O') selection range on the timeline."""

    in_ms: int | None = Field(default=None, ge=0)
    out_ms: int | None = Field(default=None, ge=0)

    @property
    def active(self) -> bool:
        return self.in_ms is not None and self.out_ms is not None and self.out_ms > self.in_ms

    @property
    def duration_ms(self) -> int:
        if self.active and self.in_ms is not None and self.out_ms is not None:
            return self.out_ms - self.in_ms
        return 0


class TimelineMarkerManager:
    """Manages markers and In/Out range selections on the timeline."""

    def __init__(self) -> None:
        self._markers: dict[str, TimelineMarker] = {}
        self._in_out = InOutRange()

    def set_mark_in(self, position_ms: int) -> InOutRange:
        """Set Mark In point ('I')."""
        self._in_out = self._in_out.model_copy(update={"in_ms": max(0, position_ms)})
        return self._in_out

    def set_mark_out(self, position_ms: int) -> InOutRange:
        """Set Mark Out point ('O')."""
        self._in_out = self._in_out.model_copy(update={"out_ms": max(0, position_ms)})
        return self._in_out

    def clear_in_out(self) -> InOutRange:
        """Clear In/Out selection range."""
        self._in_out = InOutRange()
        return self._in_out

    @property
    def in_out(self) -> InOutRange:
        return self._in_out

    def add_marker(self, marker: TimelineMarker) -> None:
        """Add a timeline marker."""
        self._markers[marker.marker_id] = marker

    def remove_marker(self, marker_id: str) -> None:
        """Remove a marker by ID."""
        self._markers.pop(marker_id, None)

    def list_markers(self) -> list[TimelineMarker]:
        """Return all markers ordered by timeline position."""
        return sorted(self._markers.values(), key=lambda m: m.position_ms)

    def marker_positions_ms(self) -> list[int]:
        """Return list of all marker positions in ms for snapping targets."""
        positions = [m.position_ms for m in self._markers.values()]
        if self._in_out.in_ms is not None:
            positions.append(self._in_out.in_ms)
        if self._in_out.out_ms is not None:
            positions.append(self._in_out.out_ms)
        return sorted(set(positions))


__all__ = [
    "InOutRange",
    "MarkerKind",
    "TimelineMarker",
    "TimelineMarkerManager",
]
