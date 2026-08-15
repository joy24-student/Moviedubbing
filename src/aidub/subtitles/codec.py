"""Bounded SRT and WebVTT parsing with an exact millisecond clock."""

from __future__ import annotations

import os
import re
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Final, Self

from pydantic import Field, model_validator

from aidub.domain.base import DomainModel
from aidub.domain.time import RationalRate, RationalTime, TimeRange
from aidub.domain.types import LanguageTag

SUBTITLE_RATE: Final = RationalRate(numerator=1_000)
DEFAULT_MAXIMUM_BYTES: Final = 32 * 1024 * 1024
DEFAULT_MAXIMUM_CUES: Final = 100_000
DEFAULT_MAXIMUM_TEXT_CHARACTERS: Final = 8_000_000
_SRT_TIMESTAMP = re.compile(
    r"^(?P<hours>[0-9]{2,}):(?P<minutes>[0-5][0-9]):(?P<seconds>[0-5][0-9]),"
    r"(?P<milliseconds>[0-9]{3})$"
)
_VTT_TIMESTAMP = re.compile(
    r"^(?:(?P<hours>[0-9]{2,}):)?(?P<minutes>[0-5][0-9]):"
    r"(?P<seconds>[0-5][0-9])\.(?P<milliseconds>[0-9]{3})$"
)


class SubtitleCodecError(ValueError):
    """Raised when subtitle input cannot be represented safely and exactly."""


class SubtitleFormat(StrEnum):
    SRT = "srt"
    WEBVTT = "webvtt"


class SubtitleCue(DomainModel):
    """One ordered cue on the exact 1 kHz subtitle time base."""

    cue_id: str | None = Field(default=None, min_length=1, max_length=512)
    time_range: TimeRange
    text: str = Field(min_length=1, max_length=100_000)
    settings: str = Field(default="", max_length=2_048)

    @model_validator(mode="after")
    def _validate_cue(self) -> Self:
        if self.time_range.rate != SUBTITLE_RATE:
            raise ValueError("subtitle cues must use the exact 1000-ticks-per-second clock")
        if self.time_range.is_empty:
            raise ValueError("subtitle cues must have positive duration")
        if "\x00" in self.text or "\x00" in self.settings:
            raise ValueError("subtitle cues cannot contain NUL characters")
        if "\n\n" in self.text.replace("\r\n", "\n"):
            raise ValueError("subtitle cue text cannot contain an empty line")
        return self


class SubtitleDocument(DomainModel):
    """A deterministic interchange document; overlapping cues remain legal."""

    format: SubtitleFormat
    language: LanguageTag | None = None
    cues: tuple[SubtitleCue, ...]

    @model_validator(mode="after")
    def _validate_order(self) -> Self:
        previous_start = -1
        identifiers: set[str] = set()
        for cue in self.cues:
            if cue.time_range.start.ticks < previous_start:
                raise ValueError("subtitle cues must be ordered by start time")
            previous_start = cue.time_range.start.ticks
            if cue.cue_id is not None:
                if cue.cue_id in identifiers:
                    raise ValueError("subtitle cue identifiers must be unique")
                identifiers.add(cue.cue_id)
        return self


def _normalize_text(source: str) -> str:
    if "\x00" in source:
        raise SubtitleCodecError("subtitle document cannot contain NUL characters")
    return source.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")


def _ticks(match: re.Match[str]) -> int:
    hours = int(match.groupdict().get("hours") or 0)
    minutes = int(match.group("minutes"))
    seconds = int(match.group("seconds"))
    milliseconds = int(match.group("milliseconds"))
    return ((hours * 60 + minutes) * 60 + seconds) * 1_000 + milliseconds


def _parse_time(value: str, pattern: re.Pattern[str], *, cue_number: int) -> int:
    match = pattern.fullmatch(value.strip())
    if match is None:
        raise SubtitleCodecError(f"cue {cue_number} has an invalid timestamp: {value!r}")
    return _ticks(match)


def _range(start: int, end: int, *, cue_number: int) -> TimeRange:
    if end <= start:
        raise SubtitleCodecError(f"cue {cue_number} must end after it starts")
    return TimeRange.from_start_end(
        RationalTime(ticks=start, rate=SUBTITLE_RATE),
        RationalTime(ticks=end, rate=SUBTITLE_RATE),
    )


def _limits(
    cues: list[SubtitleCue],
    text_characters: int,
    *,
    maximum_cues: int,
    maximum_text_characters: int,
) -> None:
    if len(cues) > maximum_cues:
        raise SubtitleCodecError(f"subtitle document exceeds {maximum_cues} cues")
    if text_characters > maximum_text_characters:
        raise SubtitleCodecError(
            f"subtitle text exceeds {maximum_text_characters} Unicode characters"
        )


def _blocks(source: str) -> tuple[str, ...]:
    normalized = _normalize_text(source).strip("\n")
    if not normalized:
        return ()
    return tuple(block for block in re.split(r"\n[ \t]*\n+", normalized) if block.strip())


def parse_srt(
    source: str,
    *,
    language: str | None = None,
    maximum_cues: int = DEFAULT_MAXIMUM_CUES,
    maximum_text_characters: int = DEFAULT_MAXIMUM_TEXT_CHARACTERS,
) -> SubtitleDocument:
    """Parse strict UTF-8 SRT text without converting timestamps to floats."""

    cues: list[SubtitleCue] = []
    text_characters = 0
    for cue_number, block in enumerate(_blocks(source), start=1):
        lines = block.split("\n")
        timing_index = 0 if "-->" in lines[0] else 1
        if len(lines) <= timing_index + 1:
            raise SubtitleCodecError(f"cue {cue_number} is incomplete")
        cue_id = None if timing_index == 0 else lines[0].strip()
        if timing_index == 1 and not cue_id:
            raise SubtitleCodecError(f"cue {cue_number} has an empty identifier")

        timing = lines[timing_index].split("-->")
        if len(timing) != 2:
            raise SubtitleCodecError(f"cue {cue_number} requires exactly one --> separator")
        end_fields = timing[1].strip().split(maxsplit=1)
        start = _parse_time(timing[0], _SRT_TIMESTAMP, cue_number=cue_number)
        end = _parse_time(end_fields[0], _SRT_TIMESTAMP, cue_number=cue_number)
        body = "\n".join(lines[timing_index + 1 :]).strip()
        if not body:
            raise SubtitleCodecError(f"cue {cue_number} has no text")
        text_characters += len(body)
        cues.append(
            SubtitleCue(
                cue_id=cue_id,
                time_range=_range(start, end, cue_number=cue_number),
                text=body,
                settings=end_fields[1] if len(end_fields) == 2 else "",
            )
        )
        _limits(
            cues,
            text_characters,
            maximum_cues=maximum_cues,
            maximum_text_characters=maximum_text_characters,
        )
    try:
        return SubtitleDocument(format=SubtitleFormat.SRT, language=language, cues=tuple(cues))
    except ValueError as exc:
        raise SubtitleCodecError(str(exc)) from exc


def _vtt_payload(source: str) -> str:
    normalized = _normalize_text(source)
    first_line, separator, remainder = normalized.partition("\n")
    if not first_line.startswith("WEBVTT"):
        raise SubtitleCodecError("WebVTT document must begin with WEBVTT")
    if first_line != "WEBVTT" and not first_line.startswith("WEBVTT "):
        raise SubtitleCodecError("invalid WebVTT header")
    if not separator:
        return ""
    # Header metadata is allowed until the first blank line.
    _metadata, metadata_separator, payload = remainder.partition("\n\n")
    return payload if metadata_separator else remainder.lstrip("\n")


def parse_webvtt(
    source: str,
    *,
    language: str | None = None,
    maximum_cues: int = DEFAULT_MAXIMUM_CUES,
    maximum_text_characters: int = DEFAULT_MAXIMUM_TEXT_CHARACTERS,
) -> SubtitleDocument:
    """Parse WebVTT cues and retain standard cue-setting text."""

    cues: list[SubtitleCue] = []
    text_characters = 0
    for cue_number, block in enumerate(_blocks(_vtt_payload(source)), start=1):
        lines = block.split("\n")
        if lines[0].startswith("NOTE"):
            continue
        if lines[0] in {"STYLE", "REGION"}:
            raise SubtitleCodecError(f"WebVTT {lines[0]} blocks are not supported in this release")
        timing_index = 0 if "-->" in lines[0] else 1
        if len(lines) <= timing_index + 1:
            raise SubtitleCodecError(f"cue {cue_number} is incomplete")
        cue_id = None if timing_index == 0 else lines[0].strip()
        timing = lines[timing_index].split("-->")
        if len(timing) != 2:
            raise SubtitleCodecError(f"cue {cue_number} requires exactly one --> separator")
        end_fields = timing[1].strip().split(maxsplit=1)
        start = _parse_time(timing[0], _VTT_TIMESTAMP, cue_number=cue_number)
        end = _parse_time(end_fields[0], _VTT_TIMESTAMP, cue_number=cue_number)
        body = "\n".join(lines[timing_index + 1 :]).strip()
        if not body:
            raise SubtitleCodecError(f"cue {cue_number} has no text")
        text_characters += len(body)
        cues.append(
            SubtitleCue(
                cue_id=cue_id,
                time_range=_range(start, end, cue_number=cue_number),
                text=body,
                settings=end_fields[1] if len(end_fields) == 2 else "",
            )
        )
        _limits(
            cues,
            text_characters,
            maximum_cues=maximum_cues,
            maximum_text_characters=maximum_text_characters,
        )
    try:
        return SubtitleDocument(format=SubtitleFormat.WEBVTT, language=language, cues=tuple(cues))
    except ValueError as exc:
        raise SubtitleCodecError(str(exc)) from exc


def _format_ticks(ticks: int, *, separator: str, always_hours: bool) -> str:
    hours, remainder = divmod(ticks, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    if always_hours or hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"
    return f"{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"


def render_srt(document: SubtitleDocument) -> str:
    """Render deterministic SRT with CRLF line endings and generated numeric indexes."""

    blocks: list[str] = []
    for index, cue in enumerate(document.cues, start=1):
        start = _format_ticks(cue.time_range.start.ticks, separator=",", always_hours=True)
        end = _format_ticks(cue.time_range.end_exclusive.ticks, separator=",", always_hours=True)
        settings = f" {cue.settings}" if cue.settings else ""
        blocks.append(f"{index}\r\n{start} --> {end}{settings}\r\n{cue.text}")
    return "\r\n\r\n".join(blocks) + ("\r\n" if blocks else "")


def render_webvtt(document: SubtitleDocument) -> str:
    """Render deterministic UTF-8 WebVTT."""

    blocks: list[str] = []
    for cue in document.cues:
        start = _format_ticks(cue.time_range.start.ticks, separator=".", always_hours=True)
        end = _format_ticks(cue.time_range.end_exclusive.ticks, separator=".", always_hours=True)
        settings = f" {cue.settings}" if cue.settings else ""
        identifier = f"{cue.cue_id}\n" if cue.cue_id else ""
        blocks.append(f"{identifier}{start} --> {end}{settings}\n{cue.text}")
    payload = "\n\n".join(blocks)
    return f"WEBVTT\n\n{payload}{'\n' if blocks else ''}"


def load_subtitle(
    path: Path | str,
    *,
    language: str | None = None,
    maximum_bytes: int = DEFAULT_MAXIMUM_BYTES,
    maximum_cues: int = DEFAULT_MAXIMUM_CUES,
) -> SubtitleDocument:
    """Load a bounded UTF-8/UTF-8-BOM subtitle file selected by extension."""

    source = Path(path).expanduser().resolve(strict=True)
    if not source.is_file():
        raise SubtitleCodecError(f"subtitle source is not a file: {source}")
    size = source.stat().st_size
    if size > maximum_bytes:
        raise SubtitleCodecError(f"subtitle file exceeds {maximum_bytes} bytes")
    try:
        text = source.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        raise SubtitleCodecError("subtitle file is not valid UTF-8") from exc
    suffix = source.suffix.casefold()
    if suffix == ".srt":
        return parse_srt(text, language=language, maximum_cues=maximum_cues)
    if suffix in {".vtt", ".webvtt"}:
        return parse_webvtt(text, language=language, maximum_cues=maximum_cues)
    raise SubtitleCodecError(f"unsupported subtitle extension: {source.suffix}")


def publish_subtitle(path: Path | str, document: SubtitleDocument) -> Path:
    """Atomically publish a new UTF-8 subtitle without replacing user data."""

    target = Path(path).expanduser().resolve(strict=False)
    if target.exists() or target.is_symlink():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix.casefold()
    if suffix == ".srt":
        payload = render_srt(document)
    elif suffix in {".vtt", ".webvtt"}:
        payload = render_webvtt(document)
    else:
        raise SubtitleCodecError(f"unsupported subtitle extension: {target.suffix}")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".staged", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target, follow_symlinks=False)
        temporary.unlink()
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return target


__all__ = [
    "DEFAULT_MAXIMUM_BYTES",
    "DEFAULT_MAXIMUM_CUES",
    "DEFAULT_MAXIMUM_TEXT_CHARACTERS",
    "SUBTITLE_RATE",
    "SubtitleCodecError",
    "SubtitleCue",
    "SubtitleDocument",
    "SubtitleFormat",
    "load_subtitle",
    "parse_srt",
    "parse_webvtt",
    "publish_subtitle",
    "render_srt",
    "render_webvtt",
]
