"""Deterministic, shell-free FFmpeg command plans for derived media.

This module only describes work.  Process execution and publication live in
``aidub.media.derivatives`` so command construction remains easy to audit and
unit test.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction
from pathlib import Path
from typing import Any, TypeAlias

from aidub.domain.time import RationalRate, RationalTime

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_HEX_COLOR_PATTERN = re.compile(r"#[0-9A-Fa-f]{6}")
_SAFE_CODEC_PATTERN = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_CACHE_SCHEMA_VERSION = 1


class DerivativeKind(StrEnum):
    """Media products supported by the first local derivative pipeline."""

    PROXY = "proxy"
    THUMBNAIL = "thumbnail"
    WAVEFORM = "waveform"


@dataclass(frozen=True, slots=True)
class ProxySpec:
    """A bounded editing proxy with an exact constant output frame rate."""

    width: int = 1280
    height: int = 720
    frame_rate: RationalRate = field(
        default_factory=lambda: RationalRate(numerator=24_000, denominator=1_001)
    )
    video_stream: int = 0
    audio_stream: int = 0
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "veryfast"
    crf: int = 23
    pixel_format: str = "yuv420p"
    audio_sample_rate: int = 48_000
    audio_channels: int = 2

    def __post_init__(self) -> None:
        if not isinstance(self.frame_rate, RationalRate):
            raise TypeError("frame_rate must be a RationalRate")
        _validate_dimensions(self.width, self.height)
        _validate_stream_index(self.video_stream)
        _validate_stream_index(self.audio_stream)
        _validate_token(self.video_codec, name="video codec")
        _validate_token(self.audio_codec, name="audio codec")
        _validate_token(self.preset, name="preset")
        _validate_token(self.pixel_format, name="pixel format")
        if not isinstance(self.crf, int) or isinstance(self.crf, bool):
            raise TypeError("CRF must be an integer")
        if not 0 <= self.crf <= 51:
            raise ValueError("CRF must be between 0 and 51")
        if not isinstance(self.audio_sample_rate, int) or isinstance(self.audio_sample_rate, bool):
            raise TypeError("audio sample rate must be an integer")
        if not 8_000 <= self.audio_sample_rate <= 768_000:
            raise ValueError("audio sample rate is outside the supported range")
        if not isinstance(self.audio_channels, int) or isinstance(self.audio_channels, bool):
            raise TypeError("audio channel count must be an integer")
        if not 1 <= self.audio_channels <= 64:
            raise ValueError("audio channel count is outside the supported range")

    @property
    def kind(self) -> DerivativeKind:
        return DerivativeKind.PROXY

    @property
    def expected_suffix(self) -> str:
        return ".mp4"

    def cache_material(self) -> dict[str, Any]:
        return {
            "audio_channels": self.audio_channels,
            "audio_codec": self.audio_codec,
            "audio_sample_rate": self.audio_sample_rate,
            "audio_stream": self.audio_stream,
            "crf": self.crf,
            "frame_rate": _rate_material(self.frame_rate),
            "height": self.height,
            "kind": self.kind.value,
            "pixel_format": self.pixel_format,
            "preset": self.preset,
            "video_codec": self.video_codec,
            "video_stream": self.video_stream,
            "width": self.width,
        }


@dataclass(frozen=True, slots=True)
class ThumbnailSpec:
    """A PNG still selected at an exact rational source time."""

    position: RationalTime
    width: int = 640
    height: int = 360
    video_stream: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.position, RationalTime):
            raise TypeError("position must be a RationalTime")
        if self.position.ticks < 0:
            raise ValueError("thumbnail position cannot be negative")
        _validate_dimensions(self.width, self.height)
        _validate_stream_index(self.video_stream)

    @property
    def kind(self) -> DerivativeKind:
        return DerivativeKind.THUMBNAIL

    @property
    def expected_suffix(self) -> str:
        return ".png"

    def cache_material(self) -> dict[str, Any]:
        return {
            "height": self.height,
            "kind": self.kind.value,
            "position": _time_material(self.position),
            "video_stream": self.video_stream,
            "width": self.width,
        }


@dataclass(frozen=True, slots=True)
class WaveformSpec:
    """A deterministic mono overview waveform rendered as a PNG."""

    width: int = 2048
    height: int = 256
    audio_stream: int = 0
    foreground_color: str = "#4A90E2"

    def __post_init__(self) -> None:
        _validate_dimensions(self.width, self.height)
        _validate_stream_index(self.audio_stream)
        if not isinstance(self.foreground_color, str):
            raise TypeError("waveform foreground color must be a string")
        if _HEX_COLOR_PATTERN.fullmatch(self.foreground_color) is None:
            raise ValueError("waveform foreground color must be a six-digit hex color")

    @property
    def kind(self) -> DerivativeKind:
        return DerivativeKind.WAVEFORM

    @property
    def expected_suffix(self) -> str:
        return ".png"

    def cache_material(self) -> dict[str, Any]:
        return {
            "audio_stream": self.audio_stream,
            "foreground_color": self.foreground_color.upper(),
            "height": self.height,
            "kind": self.kind.value,
            "width": self.width,
        }


DerivativeSpec: TypeAlias = ProxySpec | ThumbnailSpec | WaveformSpec


@dataclass(frozen=True, slots=True)
class FFmpegCommandPlan:
    """Fully expanded process arguments; consumers must execute with ``shell=False``."""

    kind: DerivativeKind
    executable: Path
    source: Path
    staged_output: Path
    argv: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.executable.is_absolute() or not self.executable.is_file():
            raise ValueError("FFmpeg executable must be an absolute existing file")
        if not self.source.is_absolute() or not self.source.is_file():
            raise ValueError("media source must be an absolute existing file")
        if not self.staged_output.is_absolute():
            raise ValueError("staged output must be an absolute path")
        if not isinstance(self.argv, tuple):
            raise TypeError("argv must be an immutable tuple")
        if not self.argv or self.argv[0] != str(self.executable):
            raise ValueError("argv must start with the declared FFmpeg executable")
        if self.argv[-1] != str(self.staged_output):
            raise ValueError("argv must end with the declared staged output")
        if any("\x00" in argument for argument in self.argv):
            raise ValueError("process arguments cannot contain NUL bytes")


def derivative_cache_key(
    source_sha256: str,
    spec: DerivativeSpec,
    *,
    ffmpeg_version: str,
) -> str:
    """Return a stable key for the source bytes, settings, and engine version."""

    normalized_hash = source_sha256.lower()
    if _SHA256_PATTERN.fullmatch(normalized_hash) is None:
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    if not ffmpeg_version.strip():
        raise ValueError("FFmpeg version cannot be empty")
    payload = {
        "cache_schema": _CACHE_SCHEMA_VERSION,
        "engine": {"id": "ffmpeg", "version": ffmpeg_version.strip()},
        "source_sha256": normalized_hash,
        "spec": spec.cache_material(),
    }
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_ffmpeg_command(
    executable: Path | str,
    source: Path | str,
    staged_output: Path | str,
    spec: DerivativeSpec,
) -> FFmpegCommandPlan:
    """Build a typed command without invoking a command shell."""

    executable_path = Path(executable).expanduser().resolve(strict=True)
    source_path = Path(source).expanduser().resolve(strict=True)
    output_path = Path(staged_output).expanduser().resolve(strict=False)
    if not executable_path.is_file():
        raise FileNotFoundError(f"FFmpeg executable is not a file: {executable_path}")
    if not source_path.is_file():
        raise FileNotFoundError(f"media source is not a file: {source_path}")
    if source_path == output_path:
        raise ValueError("source and staged output must be different files")

    common = (
        str(executable_path),
        "-hide_banner",
        "-nostdin",
        "-loglevel",
        "error",
        "-progress",
        "pipe:1",
        "-stats_period",
        "0.25",
        "-n",
        "-i",
        str(source_path),
    )
    if isinstance(spec, ProxySpec):
        arguments = _proxy_arguments(spec)
    elif isinstance(spec, ThumbnailSpec):
        arguments = _thumbnail_arguments(spec)
    elif isinstance(spec, WaveformSpec):
        arguments = _waveform_arguments(spec)
    else:
        raise TypeError(f"unsupported derivative specification: {type(spec).__name__}")
    argv = (*common, *arguments, str(output_path))
    return FFmpegCommandPlan(
        kind=spec.kind,
        executable=executable_path,
        source=source_path,
        staged_output=output_path,
        argv=argv,
    )


def _proxy_arguments(spec: ProxySpec) -> tuple[str, ...]:
    video_filter = (
        f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=decrease,"
        f"pad={spec.width}:{spec.height}:(ow-iw)/2:(oh-ih)/2,"
        f"fps=fps={_rate_text(spec.frame_rate)}:round=near"
    )
    return (
        "-map",
        f"0:v:{spec.video_stream}",
        "-map",
        f"0:a:{spec.audio_stream}?",
        "-vf",
        video_filter,
        "-c:v",
        spec.video_codec,
        "-preset",
        spec.preset,
        "-crf",
        str(spec.crf),
        "-pix_fmt",
        spec.pixel_format,
        "-c:a",
        spec.audio_codec,
        "-ar",
        str(spec.audio_sample_rate),
        "-ac",
        str(spec.audio_channels),
        "-movflags",
        "+faststart",
        "-f",
        "mp4",
    )


def _thumbnail_arguments(spec: ThumbnailSpec) -> tuple[str, ...]:
    # FFmpeg filter expressions accept rational arithmetic.  Keeping the
    # numerator/denominator avoids an early float conversion or rounded decimal.
    position = _seconds_expression(spec.position)
    video_filter = (
        f"select=gte(t\\,{position}),"
        f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=decrease,"
        f"pad={spec.width}:{spec.height}:(ow-iw)/2:(oh-ih)/2"
    )
    return (
        "-map",
        f"0:v:{spec.video_stream}",
        "-an",
        "-vf",
        video_filter,
        "-frames:v",
        "1",
        "-update",
        "1",
        "-f",
        "image2",
    )


def _waveform_arguments(spec: WaveformSpec) -> tuple[str, ...]:
    audio_filter = (
        f"[0:a:{spec.audio_stream}]aformat=channel_layouts=mono,"
        f"showwavespic=s={spec.width}x{spec.height}:colors={spec.foreground_color.upper()}"
        "[waveform]"
    )
    return (
        "-filter_complex",
        audio_filter,
        "-map",
        "[waveform]",
        "-frames:v",
        "1",
        "-update",
        "1",
        "-f",
        "image2",
    )


def _rate_text(rate: RationalRate) -> str:
    return f"{rate.numerator}/{rate.denominator}"


def _seconds_expression(value: RationalTime) -> str:
    seconds = Fraction(value.ticks * value.rate.denominator, value.rate.numerator)
    return f"{seconds.numerator}/{seconds.denominator}"


def _rate_material(rate: RationalRate) -> dict[str, int]:
    return {"denominator": rate.denominator, "numerator": rate.numerator}


def _time_material(value: RationalTime) -> dict[str, Any]:
    return {"rate": _rate_material(value.rate), "ticks": value.ticks}


def _validate_dimensions(width: int, height: int) -> None:
    if (
        not isinstance(width, int)
        or isinstance(width, bool)
        or not isinstance(height, int)
        or isinstance(height, bool)
    ):
        raise TypeError("dimensions must be integers")
    if not 16 <= width <= 16_384 or not 16 <= height <= 16_384:
        raise ValueError("dimensions must be between 16 and 16384 pixels")
    if width % 2 or height % 2:
        raise ValueError("dimensions must be even")


def _validate_stream_index(index: int) -> None:
    if not isinstance(index, int) or isinstance(index, bool):
        raise TypeError("stream index must be an integer")
    if index < 0:
        raise ValueError("stream index cannot be negative")


def _validate_token(value: str, *, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if _SAFE_CODEC_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} contains unsupported characters")


__all__ = [
    "DerivativeKind",
    "DerivativeSpec",
    "FFmpegCommandPlan",
    "ProxySpec",
    "ThumbnailSpec",
    "WaveformSpec",
    "build_ffmpeg_command",
    "derivative_cache_key",
]
