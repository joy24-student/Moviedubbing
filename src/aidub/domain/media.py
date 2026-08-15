"""Source and derived media inventory schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from .base import DomainModel, UtcDatetime, utc_now
from .identifiers import MediaAssetId, ProjectId
from .time import RationalRate, RationalTime
from .types import LanguageTag, MimeType, NonEmptyStr, Sha256


class MediaAssetKind(StrEnum):
    SOURCE = "source"
    MANAGED_SOURCE = "managed_source"
    PROXY = "proxy"
    AUDIO_STEM = "audio_stem"
    SUBTITLE = "subtitle"
    THUMBNAIL = "thumbnail"
    WAVEFORM = "waveform"
    RENDER = "render"


class MediaAvailability(StrEnum):
    ONLINE = "online"
    MISSING = "missing"
    RELINK_REQUIRED = "relink_required"
    UNVERIFIED = "unverified"


class FrameRateMode(StrEnum):
    CONSTANT = "constant"
    VARIABLE = "variable"
    UNKNOWN = "unknown"


class MediaFingerprint(DomainModel):
    """Fast identity is available immediately; full hash may arrive asynchronously."""

    fast_fingerprint: Sha256
    full_sha256: Sha256 | None = None
    byte_length: int = Field(ge=0)


class VideoStream(DomainModel):
    kind: Literal["video"] = "video"
    stream_index: int = Field(ge=0)
    codec_name: NonEmptyStr
    codec_profile: str | None = Field(default=None, max_length=128)
    width: int = Field(gt=0, le=65_535)
    height: int = Field(gt=0, le=65_535)
    pts_rate: RationalRate
    average_frame_rate: RationalRate | None = None
    real_frame_rate: RationalRate | None = None
    frame_rate_mode: FrameRateMode = FrameRateMode.UNKNOWN
    start_pts: int = 0
    duration: RationalTime | None = None
    pixel_format: str | None = Field(default=None, max_length=64)
    color_primaries: str | None = Field(default=None, max_length=64)
    color_transfer: str | None = Field(default=None, max_length=64)
    color_matrix: str | None = Field(default=None, max_length=64)
    color_range: str | None = Field(default=None, max_length=32)
    rotation_degrees: int = Field(default=0, json_schema_extra={"enum": [0, 90, 180, 270]})
    sample_aspect_ratio: str | None = Field(default=None, pattern=r"^[1-9][0-9]*:[1-9][0-9]*$")
    interlaced: bool = False
    hdr: bool = False

    @field_validator("rotation_degrees")
    @classmethod
    def _supported_rotation(cls, value: int) -> int:
        if value not in {0, 90, 180, 270}:
            raise ValueError("rotation must be 0, 90, 180, or 270 degrees")
        return value

    @model_validator(mode="after")
    def _validate_duration(self) -> Self:
        if self.duration is not None and self.duration.ticks < 0:
            raise ValueError("stream duration cannot be negative")
        return self


class AudioStream(DomainModel):
    kind: Literal["audio"] = "audio"
    stream_index: int = Field(ge=0)
    codec_name: NonEmptyStr
    sample_rate: int = Field(gt=0, le=768_000)
    channel_count: int = Field(gt=0, le=64)
    channel_layout: NonEmptyStr
    pts_rate: RationalRate
    start_pts: int = 0
    duration: RationalTime | None = None
    language: LanguageTag | None = None

    @model_validator(mode="after")
    def _validate_duration(self) -> Self:
        if self.duration is not None and self.duration.ticks < 0:
            raise ValueError("stream duration cannot be negative")
        return self


class SubtitleStream(DomainModel):
    kind: Literal["subtitle"] = "subtitle"
    stream_index: int = Field(ge=0)
    codec_name: NonEmptyStr
    pts_rate: RationalRate
    language: LanguageTag | None = None
    forced: bool = False
    hearing_impaired: bool = False


MediaStream = Annotated[VideoStream | AudioStream | SubtitleStream, Field(discriminator="kind")]


class MediaAsset(DomainModel):
    """Catalog entry; a record never grants permission to mutate the referenced bytes."""

    media_asset_id: MediaAssetId
    project_id: ProjectId
    kind: MediaAssetKind
    display_name: NonEmptyStr
    uri: NonEmptyStr
    mime_type: MimeType | None = None
    availability: MediaAvailability = MediaAvailability.UNVERIFIED
    fingerprint: MediaFingerprint
    duration: RationalTime | None = None
    streams: tuple[MediaStream, ...] = ()
    source_asset_id: MediaAssetId | None = None
    managed_copy: bool = False
    imported_at: UtcDatetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _validate_asset(self) -> Self:
        if self.duration is not None and self.duration.ticks < 0:
            raise ValueError("asset duration cannot be negative")
        indexes = tuple(stream.stream_index for stream in self.streams)
        if len(indexes) != len(set(indexes)):
            raise ValueError("media stream indexes must be unique within an asset")
        if self.kind in {MediaAssetKind.SOURCE, MediaAssetKind.MANAGED_SOURCE}:
            if self.source_asset_id is not None:
                raise ValueError("source assets cannot derive from another media asset")
            if not self.streams:
                raise ValueError("source assets must contain at least one probed stream")
        derived_kinds = {
            MediaAssetKind.PROXY,
            MediaAssetKind.AUDIO_STEM,
            MediaAssetKind.THUMBNAIL,
            MediaAssetKind.WAVEFORM,
        }
        if self.kind in derived_kinds and self.source_asset_id is None:
            raise ValueError(f"{self.kind.value} assets require a source asset")
        if self.kind is MediaAssetKind.MANAGED_SOURCE and not self.managed_copy:
            raise ValueError("managed source assets must be marked as managed copies")
        if self.kind is MediaAssetKind.SOURCE and self.managed_copy:
            raise ValueError("external source assets cannot be marked as managed copies")
        return self


__all__ = [
    "AudioStream",
    "FrameRateMode",
    "MediaAsset",
    "MediaAssetKind",
    "MediaAvailability",
    "MediaFingerprint",
    "MediaStream",
    "SubtitleStream",
    "VideoStream",
]
