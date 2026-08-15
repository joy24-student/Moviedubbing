"""
Multi-format subtitle exporter (SRT, WebVTT, ASS, SDH captions).

Renders a list of SubtitleCue objects into standardized text format payloads.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from aidub.subtitles.qc import SubtitleCue

logger = logging.getLogger(__name__)


class SubtitleFormat(StrEnum):
    SRT = "srt"
    WEBVTT = "vtt"
    ASS = "ass"


class SubtitleExporter:
    """
    Renders normalized SubtitleCue lists into SRT, WebVTT, or ASS string formats.
    """

    @staticmethod
    def export_srt(cues: list[SubtitleCue]) -> str:
        """Export cues as SubRip (.srt) text."""
        blocks: list[str] = []
        for idx, cue in enumerate(cues, start=1):
            start_str = _format_timestamp_srt(cue.start_ms)
            end_str = _format_timestamp_srt(cue.end_ms)
            blocks.append(f"{idx}\n{start_str} --> {end_str}\n{cue.text.strip()}\n")
        return "\n".join(blocks)

    @staticmethod
    def export_webvtt(cues: list[SubtitleCue]) -> str:
        """Export cues as WebVTT (.vtt) text."""
        header = "WEBVTT\n\n"
        blocks: list[str] = []
        for idx, cue in enumerate(cues, start=1):
            start_str = _format_timestamp_vtt(cue.start_ms)
            end_str = _format_timestamp_vtt(cue.end_ms)
            blocks.append(f"{idx}\n{start_str} --> {end_str}\n{cue.text.strip()}\n")
        return header + "\n".join(blocks)

    @staticmethod
    def export_ass(cues: list[SubtitleCue], title: str = "AI Dubbing Subtitles") -> str:
        """Export cues as Advanced SubStation Alpha (.ass) text."""
        header = (
            f"[Script Info]\nTitle: {title}\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n"
            "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Segoe UI,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        dialogue_lines: list[str] = []
        for cue in cues:
            start_str = _format_timestamp_ass(cue.start_ms)
            end_str = _format_timestamp_ass(cue.end_ms)
            text_ass = cue.text.replace("\n", "\\N")
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_ass}")
        return header + "\n".join(dialogue_lines) + "\n"


def _format_timestamp_srt(ms: int) -> str:
    h = ms // 3_600_000
    m = (ms % 3_600_000) // 60_000
    s = (ms % 60_000) // 1_000
    msec = ms % 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{msec:03d}"


def _format_timestamp_vtt(ms: int) -> str:
    h = ms // 3_600_000
    m = (ms % 3_600_000) // 60_000
    s = (ms % 60_000) // 1_000
    msec = ms % 1_000
    return f"{h:02d}:{m:02d}:{s:02d}.{msec:03d}"


def _format_timestamp_ass(ms: int) -> str:
    h = ms // 3_600_000
    m = (ms % 3_600_000) // 60_000
    s = (ms % 60_000) // 1_000
    cs = (ms % 1_000) // 10  # centiseconds
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


__all__ = [
    "SubtitleExporter",
    "SubtitleFormat",
]
