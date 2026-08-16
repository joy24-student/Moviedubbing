"""
Analysis Center screen.

Shows the movie analysis pipeline with animated progress for each stage,
result stat cards, warnings panel, and controls (Pause/Cancel/Background).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import QTimer, Qt, Signal
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
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


if _QT:

    _PIPELINE_STAGES = [
        ("Scene Detection", "Completed", 100, "#22C55E"),
        ("Audio Analysis", "Completed", 100, "#22C55E"),
        ("Speech Recognition", "Completed", 100, "#22C55E"),
        ("Speaker Diarization", "Processing", 74, "#4F8CFF"),
        ("Face Detection", "Queued", 0, "#687386"),
        ("Active Speaker Mapping", "Queued", 0, "#687386"),
        ("Emotion Analysis", "Queued", 0, "#687386"),
    ]

    _RESULT_CARDS = [
        ("🎬", "Scenes", "173"),
        ("🎞", "Shots", "1,924"),
        ("🎙", "Speakers", "14"),
        ("👥", "Characters", "11"),
        ("💬", "Dialogue Segments", "2,843"),
        ("🌐", "Languages", "English"),
        ("⏱", "Dialogue Duration", "81m 24s"),
        ("✅", "Analysis Quality", "97%"),
    ]

    _WARNINGS = [
        ("⚠", "warning", "42 overlapping dialogue segments"),
        ("⚠", "warning", "8 unidentified speakers"),
        ("⚠", "warning", "3 low-confidence scene boundaries"),
        ("ℹ", "info", "HDR source — proxy generated in SDR"),
    ]

    class _StageRow(QFrame):  # type: ignore[misc]
        def __init__(
            self,
            name: str,
            status: str,
            progress: int,
            color: str,
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("ElevatedPanel")
            self.setStyleSheet(
                "QFrame#ElevatedPanel{background:#1C2431;border:1px solid #283241;"
                "border-radius:8px;padding:0;}"
            )
            layout = QVBoxLayout(self)
            layout.setContentsMargins(14, 10, 14, 10)
            layout.setSpacing(6)

            top = QHBoxLayout()
            name_lbl = QLabel(name, self)
            name_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #F7F9FC;")
            top.addWidget(name_lbl)
            top.addStretch()
            status_lbl = QLabel(status, self)
            status_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {color};")
            top.addWidget(status_lbl)
            layout.addLayout(top)

            if 0 < progress < 100:
                bar = QProgressBar(self)
                bar.setRange(0, 100)
                bar.setValue(progress)
                bar.setTextVisible(False)
                bar.setFixedHeight(5)
                bar.setStyleSheet(
                    f"QProgressBar{{background:#283241;border-radius:2px;border:none;}}"
                    f"QProgressBar::chunk{{background:{color};border-radius:2px;}}"
                )
                layout.addWidget(bar)

        def update_progress(self, value: int) -> None:
            bar = self.findChild(QProgressBar)
            if bar:
                bar.setValue(value)

    class AnalysisScreen(QWidget):  # type: ignore[misc]
        """Analysis Center — movie analysis pipeline control."""

        run_analysis_requested = Signal()

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._running = True
            self._sim_progress = 74
            self._elapsed_s = 24 * 60 + 18  # 24:18
            self._build_ui()
            self._start_simulation()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background: #0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(32, 28, 32, 32)
            layout.setSpacing(24)

            # Title
            title_row = QHBoxLayout()
            title = QLabel("Analysis Center", content)
            title.setObjectName("ScreenTitle")
            title_row.addWidget(title)
            title_row.addStretch()
            self._run_btn = QPushButton("▶  Run Analysis", content)
            self._run_btn.setProperty("primary", "true")
            self._run_btn.clicked.connect(self.run_analysis_requested)
            title_row.addWidget(self._run_btn)
            layout.addLayout(title_row)

            # ---- Pipeline Stages ----
            stages_section = QVBoxLayout()
            stages_section.setSpacing(8)
            stages_label = QLabel("PIPELINE", content)
            stages_label.setObjectName("SectionLabel")
            stages_section.addWidget(stages_label)

            self._stage_rows: list[_StageRow] = []
            for name, status, pct, color in _PIPELINE_STAGES:
                row = _StageRow(name, status, pct, color, content)
                stages_section.addWidget(row)
                self._stage_rows.append(row)
            layout.addLayout(stages_section)

            # ---- Overall progress ----
            overall_frame = QFrame(content)
            overall_frame.setObjectName("Panel")
            overall_layout = QVBoxLayout(overall_frame)
            overall_layout.setContentsMargins(16, 14, 16, 14)
            overall_layout.setSpacing(8)

            pct_row = QHBoxLayout()
            pct_lbl = QLabel("Overall Progress", content)
            pct_lbl.setObjectName("PanelTitle")
            pct_row.addWidget(pct_lbl)
            pct_row.addStretch()
            self._overall_pct = QLabel("68%", content)
            self._overall_pct.setStyleSheet("font-size: 18px; font-weight: 700; color: #4F8CFF;")
            pct_row.addWidget(self._overall_pct)
            overall_layout.addLayout(pct_row)

            self._overall_bar = QProgressBar(content)
            self._overall_bar.setRange(0, 100)
            self._overall_bar.setValue(68)
            self._overall_bar.setTextVisible(False)
            self._overall_bar.setFixedHeight(10)
            overall_layout.addWidget(self._overall_bar)

            elapsed_row = QHBoxLayout()
            self._elapsed_lbl = QLabel("Elapsed  24:18", content)
            self._elapsed_lbl.setObjectName("MetaLabel")
            elapsed_row.addWidget(self._elapsed_lbl)
            elapsed_row.addStretch()
            self._eta_lbl = QLabel("Est. remaining  11:30", content)
            self._eta_lbl.setObjectName("MetaLabel")
            elapsed_row.addWidget(self._eta_lbl)
            overall_layout.addLayout(elapsed_row)

            # Controls
            ctrl_row = QHBoxLayout()
            pause_btn = QPushButton("⏸  Pause", content)
            pause_btn.clicked.connect(self._toggle_pause)
            ctrl_row.addWidget(pause_btn)
            cancel_btn = QPushButton("✕  Cancel", content)
            cancel_btn.setProperty("accent", "danger")
            ctrl_row.addWidget(cancel_btn)
            bg_btn = QPushButton("→  Background", content)
            ctrl_row.addWidget(bg_btn)
            ctrl_row.addStretch()
            overall_layout.addLayout(ctrl_row)
            layout.addWidget(overall_frame)

            # ---- Result Cards ----
            results_label = QLabel("RESULTS", content)
            results_label.setObjectName("SectionLabel")
            layout.addWidget(results_label)

            grid = QGridLayout()
            grid.setSpacing(10)
            for i, (icon, label, val) in enumerate(_RESULT_CARDS):
                card = self._stat_card(icon, label, val, content)
                grid.addWidget(card, i // 4, i % 4)
            layout.addLayout(grid)

            # ---- Warnings ----
            warn_label = QLabel("WARNINGS & NOTES", content)
            warn_label.setObjectName("SectionLabel")
            layout.addWidget(warn_label)

            for icon, tone, msg in _WARNINGS:
                warn_row = QFrame(content)
                warn_row.setStyleSheet(
                    f"QFrame{{background:#1C2431;border-left:3px solid "
                    f"{'#F59E0B' if tone=='warning' else '#4F8CFF'};"
                    f"border-radius:6px;padding:0;}}"
                )
                w_layout = QHBoxLayout(warn_row)
                w_layout.setContentsMargins(14, 8, 14, 8)
                ico = QLabel(icon, warn_row)
                ico.setStyleSheet("font-size: 14px; color: #F59E0B;" if tone == "warning" else "font-size:14px;color:#4F8CFF;")
                w_layout.addWidget(ico)
                ml = QLabel(msg, warn_row)
                ml.setStyleSheet("font-size: 13px; color: #A9B2C3;")
                ml.setCursor(Qt.CursorShape.PointingHandCursor)
                w_layout.addWidget(ml)
                w_layout.addStretch()
                layout.addWidget(warn_row)

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll)

        @staticmethod
        def _stat_card(icon: str, label: str, value: str, parent: _W) -> QFrame:
            card = QFrame(parent)
            card.setObjectName("Card")
            card.setMinimumHeight(88)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(4)
            ico = QLabel(f"{icon}  {label}", card)
            ico.setStyleSheet("font-size: 11px; color: #687386; font-weight: 600;")
            lay.addWidget(ico)
            val = QLabel(value, card)
            val.setStyleSheet("font-size: 20px; font-weight: 700; color: #F7F9FC;")
            lay.addWidget(val)
            return card

        def _toggle_pause(self) -> None:
            self._running = not self._running

        def _start_simulation(self) -> None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(1000)

        def _tick(self) -> None:
            if not self._running:
                return
            self._elapsed_s += 1
            m, s = divmod(self._elapsed_s, 60)
            self._elapsed_lbl.setText(f"Elapsed  {m:02d}:{s:02d}")

            if self._sim_progress < 100:
                self._sim_progress += 1
                # Update diarization row (index 3)
                if self._sim_progress <= 100:
                    self._stage_rows[3].update_progress(self._sim_progress)

                overall = min(100, 58 + int(self._sim_progress * 0.42))
                self._overall_bar.setValue(overall)
                self._overall_pct.setText(f"{overall}%")


__all__ = ["AnalysisScreen"]
