"""Convert probed source media into durable domain records."""

from __future__ import annotations

import mimetypes
from fractions import Fraction
from pathlib import Path
from typing import Protocol

from aidub.domain.identifiers import new_id
from aidub.domain.media import (
    AudioStream,
    FrameRateMode,
    MediaAsset,
    MediaAssetKind,
    MediaAvailability,
    MediaFingerprint,
    SubtitleStream,
    VideoStream,
)
from aidub.domain.time import RationalRate, RationalTime

from .fingerprint import full_fingerprint
from .probe import ContainerInfo, MediaProbe

_ISO_639_TO_BCP47 = {
    "eng": "en",
    "ben": "bn",
    "bn": "bn",
    "hin": "hi",
    "hindi": "hi",
    "spa": "es",
    "fra": "fr",
    "fre": "fr",
    "deu": "de",
    "ger": "de",
    "jpn": "ja",
    "kor": "ko",
    "zho": "zh",
    "chi": "zh",
}


class ProbeClient(Protocol):
    """Narrow boundary used by media import and deterministic tests."""

    def probe(self, source: Path | str) -> ContainerInfo:
        """Return bounded container metadata for a local source."""


def _language(value: str | None) -> str | None:
    if not value or value.casefold() in {"und", "unknown"}:
        return None
    return _ISO_639_TO_BCP47.get(value.casefold(), value)


def _rate_from_time_base(value: Fraction | None) -> RationalRate:
    if value is None or value <= 0:
        raise ValueError("media stream has no valid time base")
    inverse = 1 / value
    return RationalRate(numerator=inverse.numerator, denominator=inverse.denominator)


def _rate(value: Fraction | None) -> RationalRate | None:
    if value is None or value <= 0:
        return None
    return RationalRate(numerator=value.numerator, denominator=value.denominator)


def _duration(ticks: int | None, rate: RationalRate) -> RationalTime | None:
    if ticks is None or ticks < 0:
        return None
    return RationalTime(ticks=ticks, rate=rate)


class MediaImportService:
    def __init__(self, probe: ProbeClient | None = None) -> None:
        self.probe = probe or MediaProbe()

    def inspect(
        self,
        source: Path | str,
        *,
        project_id: str,
    ) -> MediaAsset:
        source_path = Path(source).expanduser().resolve(strict=True)
        info = self.probe.probe(source_path)
        fingerprint = full_fingerprint(source_path)
        streams = self._streams(info)
        if not streams:
            raise ValueError("source contains no supported audio, video, or subtitle streams")
        duration = self._container_duration(info, streams[0].pts_rate)
        mime_type = mimetypes.guess_type(source_path.name)[0]
        return MediaAsset(
            media_asset_id=new_id("med"),
            project_id=project_id,
            kind=MediaAssetKind.SOURCE,
            display_name=source_path.name,
            uri=source_path.as_uri(),
            mime_type=mime_type if mime_type and "/" in mime_type else None,
            availability=MediaAvailability.ONLINE,
            fingerprint=MediaFingerprint(
                fast_fingerprint=fingerprint.fast_sha256,
                full_sha256=fingerprint.full_sha256,
                byte_length=fingerprint.byte_length,
            ),
            duration=duration,
            streams=streams,
        )

    @staticmethod
    def _container_duration(info: ContainerInfo, rate: RationalRate) -> RationalTime | None:
        if info.duration_seconds is None or info.duration_seconds < 0:
            return None
        seconds = Fraction(str(info.duration_seconds))
        ticks = seconds * rate.fraction
        if ticks.denominator != 1:
            return None
        return RationalTime(ticks=ticks.numerator, rate=rate)

    @staticmethod
    def _streams(
        info: ContainerInfo,
    ) -> tuple[VideoStream | AudioStream | SubtitleStream, ...]:
        result: list[VideoStream | AudioStream | SubtitleStream] = []
        for video_stream in info.video_streams:
            if video_stream.width <= 0 or video_stream.height <= 0:
                continue
            pts_rate = _rate_from_time_base(video_stream.time_base)
            rotation = (video_stream.rotation_degrees or 0) % 360
            if rotation not in {0, 90, 180, 270}:
                rotation = 0
            result.append(
                VideoStream(
                    stream_index=video_stream.index,
                    codec_name=video_stream.codec,
                    width=video_stream.width,
                    height=video_stream.height,
                    pts_rate=pts_rate,
                    average_frame_rate=_rate(video_stream.average_frame_rate),
                    real_frame_rate=_rate(video_stream.real_frame_rate),
                    frame_rate_mode=(
                        FrameRateMode.VARIABLE
                        if video_stream.likely_variable_frame_rate
                        else FrameRateMode.CONSTANT
                    ),
                    start_pts=video_stream.start_ticks or 0,
                    duration=_duration(video_stream.duration_ticks, pts_rate),
                    pixel_format=video_stream.pixel_format,
                    color_primaries=video_stream.color_primaries,
                    color_transfer=video_stream.color_transfer,
                    color_matrix=video_stream.color_space,
                    color_range=video_stream.color_range,
                    rotation_degrees=rotation,
                    sample_aspect_ratio=video_stream.sample_aspect_ratio,
                    interlaced=video_stream.field_order not in {None, "unknown", "progressive"},
                    hdr=video_stream.color_transfer in {"smpte2084", "arib-std-b67"},
                )
            )
        for audio_stream in info.audio_streams:
            if not audio_stream.sample_rate or not audio_stream.channels:
                continue
            pts_rate = _rate_from_time_base(audio_stream.time_base)
            result.append(
                AudioStream(
                    stream_index=audio_stream.index,
                    codec_name=audio_stream.codec,
                    sample_rate=audio_stream.sample_rate,
                    channel_count=audio_stream.channels,
                    channel_layout=audio_stream.channel_layout
                    or f"{audio_stream.channels} channels",
                    pts_rate=pts_rate,
                    start_pts=audio_stream.start_ticks or 0,
                    duration=_duration(audio_stream.duration_ticks, pts_rate),
                    language=_language(audio_stream.language),
                )
            )
        result.extend(
            SubtitleStream(
                stream_index=stream.index,
                codec_name=stream.codec,
                pts_rate=_rate_from_time_base(stream.time_base),
                language=_language(stream.language),
                forced=stream.forced,
                hearing_impaired=stream.hearing_impaired,
            )
            for stream in info.subtitle_streams
        )
        return tuple(sorted(result, key=lambda item: item.stream_index))
