"""
Export Center screen.

Preset cards + format options + multi-language MKV export.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W

_PRESETS = [
    ("🎬", "Cinema Master",  "4K HDR · Original streams\nAll languages · QC verified", True),
    ("📺", "Streaming",      "1080p · AAC 5.1\nAll dub languages", False),
    ("▶",  "YouTube",        "1080p / 4K · AAC stereo\nBurned subtitles optional", False),
    ("📱", "Mobile",         "720p · AAC stereo\nCompact file size", False),
    ("🎧", "Audio Dub Only", "WAV stems per language\nNo video stream", False),
    ("💬", "Subtitle Only",  "SRT + VTT + ASS\nAll languages", False),
    ("⚙",  "Custom",         "Choose all settings\nmanually", False),
]

_AUDIO_TRACKS = [
    ("English", "Original", True),
    ("Bengali", "AAC 5.1 640 kbps", True),
    ("Hindi",   "AAC 5.1 640 kbps", True),
    ("Spanish", "AAC 5.1 640 kbps", False),
]

_SUBTITLE_TRACKS = [
    ("English", True),
    ("Bengali", True),
    ("Hindi",   True),
    ("Spanish", False),
]


if _QT:

    class _PresetCard(QFrame):  # type: ignore[misc]
        def __init__(
            self,
            icon: str,
            title: str,
            desc: str,
            recommended: bool,
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("PresetCard")
            self.setFixedSize(165, 140)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self._selected = False

            lay = QVBoxLayout(self)
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(6)

            icon_lbl = QLabel(icon, self)
            icon_lbl.setStyleSheet("font-size:28px;background:transparent;border:none;")
            lay.addWidget(icon_lbl)

            row = QHBoxLayout()
            t = QLabel(title, self)
            t.setStyleSheet("font-size:12px;font-weight:700;color:#F7F9FC;")
            row.addWidget(t)
            if recommended:
                badge = QLabel("★", self)
                badge.setStyleSheet("color:#F59E0B;font-size:12px;")
                row.addWidget(badge)
            row.addStretch()
            lay.addLayout(row)

            d = QLabel(desc, self)
            d.setStyleSheet("font-size:11px;color:#687386;")
            d.setWordWrap(True)
            lay.addWidget(d)

            self._refresh_style()

        def _refresh_style(self) -> None:
            if self._selected:
                self.setStyleSheet(
                    "QFrame#PresetCard{background:#1E3A5F;border:2px solid #4F8CFF;border-radius:10px;}"
                )
            else:
                self.setStyleSheet(
                    "QFrame#PresetCard{background:#161D28;border:1px solid #283241;border-radius:10px;}"
                    "QFrame#PresetCard:hover{border-color:#34415A;}"
                )

        def set_selected(self, sel: bool) -> None:
            self._selected = sel
            self._refresh_style()

        def mousePressEvent(self, _event: object) -> None:  # noqa: N802
            pass  # handled by parent

    class ExportScreen(QWidget):  # type: ignore[misc]
        """Export Center — presets, format options, multi-language."""

        export_started = Signal(dict)

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._preset_cards: list[_PresetCard] = []
            self._selected_preset = 0
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            topbar = QFrame(self)
            topbar.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;")
            topbar.setFixedHeight(48)
            tb = QHBoxLayout(topbar)
            tb.setContentsMargins(16, 0, 16, 0)
            lbl = QLabel("Export Center", self)
            lbl.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(lbl)
            tb.addStretch()
            root.addWidget(topbar)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 24)
            layout.setSpacing(20)

            # ── Preset Cards ───────────────────────────────────────────
            layout.addWidget(self._section("EXPORT PRESET"))
            presets_row = QHBoxLayout()
            presets_row.setSpacing(10)
            for i, (icon, title, desc, rec) in enumerate(_PRESETS):
                card = _PresetCard(icon, title, desc, rec, content)
                card.mousePressEvent = lambda _e, idx=i: self._select_preset(idx)  # type: ignore[method-assign]
                presets_row.addWidget(card)
                self._preset_cards.append(card)
            presets_row.addStretch()
            layout.addLayout(presets_row)
            self._select_preset(0)

            # ── Format Options ─────────────────────────────────────────
            fmt_group = QGroupBox("Format Options", content)
            fmt_grid = QGridLayout(fmt_group)
            fmt_grid.setSpacing(12)
            fmt_grid.setContentsMargins(16, 16, 16, 16)

            rows = [
                ("Container",   ["MKV", "MP4", "MOV", "WebM"]),
                ("Video",       ["Copy Original Stream", "H.265 4K", "H.265 1080p", "H.264 1080p"]),
                ("Frame Rate",  ["Source (23.976)", "24 fps", "25 fps", "30 fps"]),
                ("Loudness",    ["-23 LUFS (EBU R128)", "-24 LUFS (Netflix)", "-14 LUFS (YouTube)"]),
            ]
            for i, (label, opts) in enumerate(rows):
                fmt_grid.addWidget(self._k_lbl(label, fmt_group), i, 0)
                combo = QComboBox(fmt_group)
                combo.addItems(opts)
                combo.setMinimumWidth(220)
                fmt_grid.addWidget(combo, i, 1)
            layout.addWidget(fmt_group)

            # ── Audio Tracks ───────────────────────────────────────────
            audio_group = QGroupBox("Audio Tracks", content)
            audio_lay = QVBoxLayout(audio_group)
            audio_lay.setContentsMargins(16, 14, 16, 14)
            audio_lay.setSpacing(8)
            for lang, spec, checked in _AUDIO_TRACKS:
                row = QHBoxLayout()
                cb = QCheckBox(f"{lang}  —  {spec}", audio_group)
                cb.setChecked(checked)
                row.addWidget(cb)
                row.addStretch()
                audio_lay.addLayout(row)
            layout.addWidget(audio_group)

            # ── Subtitle Tracks ────────────────────────────────────────
            sub_group = QGroupBox("Subtitle Tracks", content)
            sub_lay = QHBoxLayout(sub_group)
            sub_lay.setContentsMargins(16, 14, 16, 14)
            for lang, checked in _SUBTITLE_TRACKS:
                cb = QCheckBox(lang, sub_group)
                cb.setChecked(checked)
                sub_lay.addWidget(cb)
            sub_lay.addStretch()
            layout.addWidget(sub_group)

            # ── Output path ────────────────────────────────────────────
            path_group = QGroupBox("Output", content)
            path_lay = QHBoxLayout(path_group)
            path_lay.setContentsMargins(16, 12, 16, 12)
            self._path_edit = QLineEdit("D:\\Exports\\Movie_Bengali_Final.mkv", path_group)
            path_lay.addWidget(self._path_edit, 1)
            browse_btn = QPushButton("Browse…", path_group)
            browse_btn.setFixedWidth(90)
            browse_btn.clicked.connect(self._browse_path)
            path_lay.addWidget(browse_btn)
            layout.addWidget(path_group)

            # ── Export button ──────────────────────────────────────────
            export_btn = QPushButton("🚀  Start Export", content)
            export_btn.setProperty("primary", "true")
            export_btn.setFixedHeight(46)
            export_btn.clicked.connect(self._on_export)
            layout.addWidget(export_btn)

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll, 1)

        def _select_preset(self, idx: int) -> None:
            self._selected_preset = idx
            for i, card in enumerate(self._preset_cards):
                card.set_selected(i == idx)

        def _browse_path(self) -> None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Output", self._path_edit.text(),
                "MKV Files (*.mkv);;MP4 Files (*.mp4);;All Files (*)"
            )
            if path:
                self._path_edit.setText(path)

        def _on_export(self) -> None:
            self.export_started.emit({
                "preset": self._selected_preset,
                "output": self._path_edit.text(),
            })

        @staticmethod
        def _section(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("SectionLabel")
            return lbl

        @staticmethod
        def _k_lbl(text: str, parent: QWidget) -> QLabel:
            lbl = QLabel(text, parent)
            lbl.setObjectName("MetaLabel")
            return lbl


__all__ = ["ExportScreen"]
