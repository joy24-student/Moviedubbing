"""
High-density video thumbnail strip generator & frame cache provider.

Provides downsampled video frame thumbnails for video tracks V1 and V2
during scrubbing and zoom operations on the multitrack timeline.
"""

from __future__ import annotations

import logging

from pydantic import Field

from aidub.contracts.base import ContractModel

logger = logging.getLogger(__name__)


class VideoThumbnailFrame(ContractModel):
    """Metadata & cache key for a single video thumbnail frame."""

    frame_index: int = Field(ge=0)
    pts_ms: int = Field(ge=0)
    image_cache_key: str = Field(min_length=1, max_length=128)
    width_px: int = Field(default=160, ge=32)
    height_px: int = Field(default=90, ge=18)


class ThumbnailStripData(ContractModel):
    """Thumbnail strip for a video clip on track V1/V2."""

    clip_id: str
    frames: list[VideoThumbnailFrame] = Field(default_factory=list)
    interval_ms: int = Field(default=1000, ge=100)


class ThumbnailCacheManager:
    """
    LRU cache manager for video thumbnail frames during scrubbing.
    """

    def __init__(self, max_cache_size: int = 500) -> None:
        self._max_size = max_cache_size
        self._cache: dict[str, VideoThumbnailFrame] = {}

    def get_thumbnail(
        self, clip_id: str, pts_ms: int, interval_ms: int = 1000, fps: float = 24.0
    ) -> VideoThumbnailFrame:
        """Get or generate thumbnail frame metadata for a timestamp."""
        frame_idx = int((pts_ms / 1000.0) * fps)
        key = f"{clip_id}_{frame_idx}"

        if key in self._cache:
            return self._cache[key]

        frame = VideoThumbnailFrame(
            frame_index=frame_idx,
            pts_ms=pts_ms,
            image_cache_key=f"thumb_{key}",
        )

        if len(self._cache) >= self._max_size:
            # Evict oldest entry
            oldest = next(iter(self._cache))
            self._cache.pop(oldest, None)

        self._cache[key] = frame
        return frame

    def generate_strip(
        self, clip_id: str, duration_ms: int, interval_ms: int = 1000, fps: float = 24.0
    ) -> ThumbnailStripData:
        """Generate complete thumbnail strip for a video clip."""
        frames: list[VideoThumbnailFrame] = []
        for pts_ms in range(0, duration_ms, max(100, interval_ms)):
            frames.append(self.get_thumbnail(clip_id, pts_ms, interval_ms, fps))

        return ThumbnailStripData(
            clip_id=clip_id,
            frames=frames,
            interval_ms=interval_ms,
        )


__all__ = [
    "ThumbnailCacheManager",
    "ThumbnailStripData",
    "VideoThumbnailFrame",
]
