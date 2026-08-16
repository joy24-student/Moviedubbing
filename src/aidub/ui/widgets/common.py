"""
Shared UI widgets used across multiple screens.

Includes:
- ScoreBadge: colored score % label with automatic green/amber/red levels
- WaveformWidget: painted waveform display
- GpuPopover: GPU monitor popover
- SectionHeader: standardized section title + subtitle
- PanelFrame: styled panel container
- EmptyStateWidget: empty-state placeholder with icon and CTA button
- HRule / VRule: dividers
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
    from PySide6.QtGui import (
        QColor,
        QFont,
        QPainter,
        QPen,
        QPolygon,
    )
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


# ---------------------------------------------------------------------------
# Colour constants (mirrors styles.py tokens)
# ---------------------------------------------------------------------------
_SUCCESS = "#22C55E"
_WARNING = "#F59E0B"
_DANGER = "#EF4444"
_PRIMARY = "#4F8CFF"
_AI_VIOLET = "#8B5CF6"
_PANEL = "#161D28"
_ELEVATED = "#1C2431"
_BORDER = "#283241"
_TEXT_PRIMARY = "#F7F9FC"
_TEXT_SECONDARY = "#A9B2C3"
_TEXT_MUTED = "#687386"


def _score_level(score: float) -> str:
    """Return 'high', 'mid', or 'low' level string for a 0-100 score."""
    if score >= 85:
        return "high"
    if score >= 65:
        return "mid"
    return "low"


if _QT:

    # ------------------------------------------------------------------
    # ScoreBadge
    # ------------------------------------------------------------------
    class ScoreBadge(QLabel):  # type: ignore[misc]
        """Colored score % badge: green ≥85%, amber ≥65%, red <65%."""

        def __init__(self, score: float = 0.0, suffix: str = "%", parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("ScoreBadge")
            self._suffix = suffix
            self.set_score(score)

        def set_score(self, score: float) -> None:
            self._score = score
            level = _score_level(score)
            self.setProperty("level", level)
            self.setText(f"{score:.0f}{self._suffix}")
            self.style().unpolish(self)
            self.style().polish(self)

    # ------------------------------------------------------------------
    # SectionHeader
    # ------------------------------------------------------------------
    class SectionHeader(QWidget):  # type: ignore[misc]
        """Screen-level header: large title + optional subtitle."""

        def __init__(self, title: str, subtitle: str = "", parent: _W | None = None) -> None:
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 4)
            layout.setSpacing(4)

            self._title_lbl = QLabel(title, self)
            self._title_lbl.setObjectName("ScreenTitle")
            layout.addWidget(self._title_lbl)

            if subtitle:
                self._sub_lbl = QLabel(subtitle, self)
                self._sub_lbl.setObjectName("MutedLabel")
                self._sub_lbl.setWordWrap(True)
                layout.addWidget(self._sub_lbl)

        def set_title(self, text: str) -> None:
            self._title_lbl.setText(text)

    # ------------------------------------------------------------------
    # PanelFrame
    # ------------------------------------------------------------------
    class PanelFrame(QFrame):  # type: ignore[misc]
        """Styled dark panel container."""

        def __init__(self, parent: _W | None = None, *, elevated: bool = False) -> None:
            super().__init__(parent)
            self.setObjectName("ElevatedPanel" if elevated else "Panel")

        def set_layout_margins(self, m: int = 12) -> None:
            if self.layout():
                self.layout().setContentsMargins(m, m, m, m)

    # ------------------------------------------------------------------
    # HRule / VRule
    # ------------------------------------------------------------------
    class HRule(QFrame):  # type: ignore[misc]
        """1px horizontal divider."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("DividerH")
            self.setFrameShape(QFrame.Shape.HLine)

    class VRule(QFrame):  # type: ignore[misc]
        """1px vertical divider."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("DividerV")
            self.setFrameShape(QFrame.Shape.VLine)

    # ------------------------------------------------------------------
    # EmptyStateWidget
    # ------------------------------------------------------------------
    class EmptyStateWidget(QWidget):  # type: ignore[misc]
        """Centered empty-state placeholder with icon, message, and optional CTA."""

        def __init__(
            self,
            icon: str,
            message: str,
            cta: str = "",
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setSpacing(12)

            icon_lbl = QLabel(icon, self)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("font-size: 40px; color: #34415A;")
            layout.addWidget(icon_lbl)

            msg_lbl = QLabel(message, self)
            msg_lbl.setObjectName("MutedLabel")
            msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_lbl.setWordWrap(True)
            msg_lbl.setMaximumWidth(320)
            layout.addWidget(msg_lbl)

            if cta:
                self.cta_btn = QPushButton(cta, self)
                self.cta_btn.setFixedWidth(180)
                layout.addWidget(self.cta_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------
    # WaveformWidget
    # ------------------------------------------------------------------
    class WaveformWidget(QWidget):  # type: ignore[misc]
        """
        Painted waveform display widget.

        Accepts a list of amplitude samples (0.0-1.0).
        If no samples provided, generates a random demo waveform.
        """

        def __init__(
            self,
            samples: list[float] | None = None,
            color: str = _PRIMARY,
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("WaveformArea")
            self.setMinimumHeight(48)
            self._color = QColor(color)
            self._samples: list[float] = samples or self._demo_samples(200)
            self._playhead_pos: float = 0.0  # 0.0 – 1.0

        @staticmethod
        def _demo_samples(n: int) -> list[float]:
            result: list[float] = []
            phase = 0.0
            for _ in range(n):
                phase += random.uniform(0.03, 0.18)
                result.append(abs(math.sin(phase)) * random.uniform(0.3, 1.0))
            return result

        def set_playhead(self, position: float) -> None:
            """Set playhead position (0.0 = start, 1.0 = end)."""
            self._playhead_pos = max(0.0, min(1.0, position))
            self.update()

        def set_samples(self, samples: list[float]) -> None:
            self._samples = samples
            self.update()

        def paintEvent(self, _event: object) -> None:  # noqa: N802
            if not self._samples:
                return
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            w, h = self.width(), self.height()
            mid = h / 2

            # Background
            painter.fillRect(0, 0, w, h, QColor("#080B10"))

            # Waveform bars
            n = len(self._samples)
            bar_w = max(1.0, w / n)
            alpha_color = QColor(self._color)
            alpha_color.setAlpha(220)
            fill_color = QColor(self._color)
            fill_color.setAlpha(80)

            for i, amp in enumerate(self._samples):
                x = int(i * bar_w)
                bar_h = amp * (mid - 2)
                # Upper bar
                painter.fillRect(int(x), int(mid - bar_h), max(1, int(bar_w) - 1), int(bar_h), fill_color)
                # Lower bar
                painter.fillRect(int(x), int(mid), max(1, int(bar_w) - 1), int(bar_h), fill_color)
                # Center line pixel
                painter.fillRect(int(x), int(mid - 1), max(1, int(bar_w) - 1), 2, alpha_color)

            # Playhead
            px = int(self._playhead_pos * w)
            pen = QPen(QColor("#F7F9FC"), 1.5)
            painter.setPen(pen)
            painter.drawLine(px, 0, px, h)
            painter.end()

    # ------------------------------------------------------------------
    # VuMeter  (vertical audio level bar)
    # ------------------------------------------------------------------
    class VuMeterWidget(QWidget):  # type: ignore[misc]
        """Simple vertical VU meter bar for the mixer."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setMinimumWidth(16)
            self.setMinimumHeight(80)
            self.setMaximumWidth(20)
            self._level: float = 0.75
            self._clipped = False

        def set_level(self, level: float) -> None:
            """Set level 0.0–1.0."""
            self._level = max(0.0, min(1.0, level))
            self._clipped = level > 1.0
            self.update()

        def paintEvent(self, _event: object) -> None:  # noqa: N802
            painter = QPainter(self)
            w, h = self.width(), self.height()

            painter.fillRect(0, 0, w, h, QColor("#080B10"))

            # Segments
            seg_h = 4
            seg_gap = 2
            n_segs = h // (seg_h + seg_gap)
            filled = int(self._level * n_segs)

            for i in range(n_segs):
                y = h - (i + 1) * (seg_h + seg_gap)
                frac = i / max(1, n_segs)
                if i < filled:
                    if frac > 0.85:
                        col = QColor(_DANGER)
                    elif frac > 0.70:
                        col = QColor(_WARNING)
                    else:
                        col = QColor(_AUDIO_GREEN := "#10B981")
                else:
                    col = QColor(_BORDER)
                painter.fillRect(2, y, w - 4, seg_h, col)
            painter.end()

    # ------------------------------------------------------------------
    # GpuPopover
    # ------------------------------------------------------------------
    class GpuPopover(QWidget):  # type: ignore[misc]
        """
        Floating GPU monitor popover widget.

        Shows GPU %, VRAM bar, temperature, and loaded models list.
        """

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent, Qt.WindowType.Popup)
            self.setObjectName("GpuPopover")
            self.setFixedWidth(280)
            self.setStyleSheet(f"""
                QWidget#GpuPopover {{
                    background: #161D28;
                    border: 1px solid #34415A;
                    border-radius: 10px;
                }}
                QLabel {{ color: #F7F9FC; }}
            """)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(10)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("🖥  GPU Monitor", self)
            title.setStyleSheet("font-size: 14px; font-weight: 700;")
            hdr.addWidget(title)
            hdr.addStretch()
            close_btn = QPushButton("✕", self)
            close_btn.setFixedSize(24, 24)
            close_btn.setStyleSheet("QPushButton{background:transparent;border:none;color:#687386;font-size:12px;}")
            close_btn.clicked.connect(self.hide)
            hdr.addWidget(close_btn)
            layout.addLayout(hdr)

            layout.addWidget(HRule(self))

            # GPU name
            self._gpu_label = QLabel("NVIDIA RTX 4070", self)
            self._gpu_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #A9B2C3;")
            layout.addWidget(self._gpu_label)

            # Stats grid
            stats = [
                ("GPU Utilization", "0%", "gpu_val"),
                ("VRAM", "0 / 12 GB", "vram_val"),
                ("Temperature", "—", "temp_val"),
            ]
            self._stat_labels: dict[str, QLabel] = {}
            for stat_name, default, key in stats:
                row = QHBoxLayout()
                name_lbl = QLabel(stat_name, self)
                name_lbl.setStyleSheet("color: #687386; font-size: 12px;")
                val_lbl = QLabel(default, self)
                val_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
                row.addWidget(name_lbl)
                row.addStretch()
                row.addWidget(val_lbl)
                layout.addLayout(row)
                self._stat_labels[key] = val_lbl

            # VRAM progress bar
            self._vram_bar = QProgressBar(self)
            self._vram_bar.setRange(0, 100)
            self._vram_bar.setValue(0)
            self._vram_bar.setTextVisible(False)
            layout.addWidget(self._vram_bar)

            layout.addWidget(HRule(self))

            # Loaded models
            models_lbl = QLabel("Loaded Models", self)
            models_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #687386; letter-spacing: 1px;")
            layout.addWidget(models_lbl)

            self._models_layout = QVBoxLayout()
            self._models_layout.setSpacing(4)
            layout.addLayout(self._models_layout)

            # Manager button
            mgr_btn = QPushButton("Open GPU Manager", self)
            mgr_btn.setStyleSheet("margin-top: 4px;")
            layout.addWidget(mgr_btn)

            # Demo data
            self.update_stats(gpu_pct=62, vram_used=8.1, vram_total=12.0, temp=72)
            self.set_models({"Whisper": 3.8, "Voice Engine": 2.4})

        def update_stats(
            self,
            gpu_pct: int = 0,
            vram_used: float = 0.0,
            vram_total: float = 12.0,
            temp: int = 0,
        ) -> None:
            self._stat_labels["gpu_val"].setText(f"{gpu_pct}%")
            self._stat_labels["vram_val"].setText(f"{vram_used:.1f} / {vram_total:.0f} GB")
            self._stat_labels["temp_val"].setText(f"{temp}°C")
            pct = int(vram_used / max(1, vram_total) * 100)
            self._vram_bar.setValue(pct)
            if pct >= 90:
                self._vram_bar.setProperty("accent", "danger")
            elif pct >= 75:
                self._vram_bar.setProperty("accent", "warning")

        def set_models(self, models: dict[str, float]) -> None:
            # Clear existing
            while self._models_layout.count():
                item = self._models_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            for model_name, size_gb in models.items():
                row = QHBoxLayout()
                n = QLabel(f"  {model_name}", self)
                n.setStyleSheet("font-size: 12px; color: #A9B2C3;")
                s = QLabel(f"{size_gb:.1f} GB", self)
                s.setStyleSheet("font-size: 12px; color: #687386;")
                row.addWidget(n)
                row.addStretch()
                row.addWidget(s)
                self._models_layout.addLayout(row)

        def show_below(self, pos: QPoint) -> None:
            self.move(pos.x() - self.width() // 2, pos.y() + 4)
            self.show()

    # ------------------------------------------------------------------
    # ProgressCard
    # ------------------------------------------------------------------
    class ProgressCard(QFrame):  # type: ignore[misc]
        """Animated job progress card."""

        def __init__(
            self,
            title: str,
            subtitle: str = "",
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("Card")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(6)

            top = QHBoxLayout()
            self._title_lbl = QLabel(title, self)
            self._title_lbl.setObjectName("PanelTitle")
            top.addWidget(self._title_lbl)
            top.addStretch()
            self._pct_lbl = QLabel("0%", self)
            self._pct_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {_PRIMARY};")
            top.addWidget(self._pct_lbl)
            layout.addLayout(top)

            if subtitle:
                self._sub_lbl = QLabel(subtitle, self)
                self._sub_lbl.setObjectName("MutedLabel")
                layout.addWidget(self._sub_lbl)

            self._bar = QProgressBar(self)
            self._bar.setRange(0, 100)
            self._bar.setTextVisible(False)
            layout.addWidget(self._bar)

        def set_progress(self, pct: int, subtitle: str = "") -> None:
            pct = max(0, min(100, pct))
            self._bar.setValue(pct)
            self._pct_lbl.setText(f"{pct}%")
            if subtitle and hasattr(self, "_sub_lbl"):
                self._sub_lbl.setText(subtitle)

    class QualityHeatmapWidget(QFrame):  # type: ignore[misc]
        """
        Timeline Quality Heatmap Bar (Master Spec Section 33).
        Renders a color-coded quality strip over project duration:
          Green:  Good (Score >= 85%)
          Yellow: Review needed (Score 65-84%)
          Red:    Critical defect / Blocking
          Blue:   Processing
          Gray:   Unanalyzed
        Emits timecode_clicked(sec: float) on click.
        """

        timecode_clicked = Signal(float)

        def __init__(self, duration_sec: float = 7940.0, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setFixedHeight(18)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip("Quality Heatmap — Click to jump to timecode")
            self._duration = duration_sec
            # List of (start_pct, end_pct, status_color)
            self._segments: list[tuple[float, float, str]] = [
                (0.00, 0.15, "#22C55E"),  # Green
                (0.15, 0.22, "#F59E0B"),  # Yellow review
                (0.22, 0.45, "#22C55E"),  # Green
                (0.45, 0.48, "#EF4444"),  # Red critical
                (0.48, 0.70, "#22C55E"),  # Green
                (0.70, 0.78, "#4F8CFF"),  # Blue processing
                (0.78, 0.85, "#F59E0B"),  # Yellow
                (0.85, 1.00, "#22C55E"),  # Green
            ]

        def paintEvent(self, event: Any) -> None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            w = self.width()
            h = self.height()

            # Background
            painter.fillRect(0, 0, w, h, QColor("#121822"))

            for start_pct, end_pct, color_hex in self._segments:
                x1 = int(start_pct * w)
                x2 = int(end_pct * w)
                seg_w = max(2, x2 - x1)
                painter.fillRect(x1, 2, seg_w, h - 4, QColor(color_hex))

            # Border
            painter.setPen(QPen(QColor("#283241"), 1))
            painter.drawRect(0, 0, w - 1, h - 1)

        def mousePressEvent(self, event: Any) -> None:
            if self.width() > 0:
                pct = max(0.0, min(1.0, event.position().x() / self.width()))
                target_sec = pct * self._duration
                self.timecode_clicked.emit(target_sec)


__all__ = [
    "EmptyStateWidget",
    "GpuPopover",
    "HRule",
    "PanelFrame",
    "ProgressCard",
    "QualityHeatmapWidget",
    "ScoreBadge",
    "SectionHeader",
    "VRule",
    "VuMeterWidget",
    "WaveformWidget",
]
