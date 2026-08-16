"""
Home Dashboard screen.

Features:
- Greeting header with time-of-day
- Quick-action buttons (New Project / Open Project / Import Movie)
- Recent Projects grid (3-column thumbnail cards)
- Current Jobs panel with live progress
- System status (GPU %, VRAM, RAM, model health)
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


def _greeting() -> str:
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    if hour < 21:
        return "Good evening"
    return "Good night"


if _QT:

    # ------------------------------------------------------------------
    # Project Card
    # ------------------------------------------------------------------
    class _ProjectCard(QFrame):  # type: ignore[misc]
        clicked = Signal(str)

        _STATUS_COLORS = {
            "Completed": "#22C55E",
            "Analysis": "#22D3EE",
            "Translating": "#A855F7",
            "Rendering": "#F59E0B",
            "Error": "#EF4444",
        }

        def __init__(
            self,
            project_id: str,
            name: str,
            language: str,
            status: str,
            progress: int = 100,
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("Card")
            self.setFixedSize(210, 140)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self._id = project_id

            layout = QVBoxLayout(self)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(6)

            # Thumbnail placeholder
            thumb = QFrame(self)
            thumb.setFixedHeight(52)
            thumb.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #1C2431,stop:1 #0D1118);"
                "border: 1px solid #283241; border-radius: 6px;"
            )
            thumb_layout = QHBoxLayout(thumb)
            film_icon = QLabel("🎬", thumb)
            film_icon.setStyleSheet("font-size: 22px; background: transparent; border: none;")
            film_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_layout.addWidget(film_icon)
            layout.addWidget(thumb)

            name_lbl = QLabel(name, self)
            name_lbl.setObjectName("PanelTitle")
            name_lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
            layout.addWidget(name_lbl)

            lang_lbl = QLabel(language, self)
            lang_lbl.setStyleSheet("font-size: 11px; color: #687386;")
            layout.addWidget(lang_lbl)

            # Status / progress
            status_color = self._STATUS_COLORS.get(status, "#A9B2C3")
            if progress < 100:
                bar = QProgressBar(self)
                bar.setRange(0, 100)
                bar.setValue(progress)
                bar.setTextVisible(False)
                bar.setFixedHeight(5)
                bar.setStyleSheet(
                    f"QProgressBar{{background:#283241;border-radius:2px;border:none;}}"
                    f"QProgressBar::chunk{{background:{status_color};border-radius:2px;}}"
                )
                layout.addWidget(bar)
            else:
                status_lbl = QLabel(status, self)
                status_lbl.setStyleSheet(
                    f"font-size: 11px; font-weight: 700; color: {status_color};"
                )
                layout.addWidget(status_lbl)

        def mousePressEvent(self, _event: object) -> None:  # noqa: N802
            self.clicked.emit(self._id)

    # ------------------------------------------------------------------
    # Job Row
    # ------------------------------------------------------------------
    class _JobRow(QFrame):  # type: ignore[misc]
        def __init__(
            self,
            title: str,
            stage: str,
            progress: int,
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
            layout.setSpacing(4)

            top_row = QHBoxLayout()
            title_lbl = QLabel(title, self)
            title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #F7F9FC;")
            top_row.addWidget(title_lbl)
            top_row.addStretch()
            pct_lbl = QLabel(f"{progress}%", self)
            pct_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #4F8CFF;")
            top_row.addWidget(pct_lbl)
            layout.addLayout(top_row)

            stage_lbl = QLabel(stage, self)
            stage_lbl.setStyleSheet("font-size: 11px; color: #687386;")
            layout.addWidget(stage_lbl)

            bar = QProgressBar(self)
            bar.setRange(0, 100)
            bar.setValue(progress)
            bar.setTextVisible(False)
            bar.setFixedHeight(5)
            layout.addWidget(bar)

    # ------------------------------------------------------------------
    # Dashboard Screen
    # ------------------------------------------------------------------
    class DashboardScreen(QWidget):  # type: ignore[misc]
        """Home Dashboard — first screen after launch."""

        new_project_requested = Signal()
        open_project_requested = Signal()
        project_opened = Signal(str)

        _RECENT_PROJECTS = [
            ("proj_1", "Avengers Endgame", "বাংলা (Bengali)", "Rendering", 72),
            ("proj_2", "The Dark Knight", "हिंदी (Hindi)", "Completed", 100),
            ("proj_3", "Interstellar Ep 04", "Español (Spanish)", "Analysis", 28),
            ("proj_4", "Oppenheimer", "العربية (Arabic)", "Translating", 55),
            ("proj_5", "Dune Part Two", "Français (French)", "Completed", 100),
            ("proj_6", "Barbie (2023)", "Deutsch (German)", "Error", 81),
        ]

        _ACTIVE_JOBS = [
            ("Avengers Bengali Dub", "Lip Sync • Scene 134 / 179", 78),
            ("Dark Knight Hindi Dub", "Audio Mixing • Finalizing stems", 94),
            ("Dune French Translation", "Voice Generation • Take 2", 43),
        ]

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            # Scrollable content
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            content = QWidget()
            content.setStyleSheet(f"background: #0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(32, 28, 32, 32)
            layout.setSpacing(28)

            # ---- Greeting ----
            greeting_section = QVBoxLayout()
            greeting_section.setSpacing(4)

            self._greeting_lbl = QLabel(_greeting(), content)
            self._greeting_lbl.setStyleSheet("font-size: 28px; font-weight: 700; color: #F7F9FC;")
            greeting_section.addWidget(self._greeting_lbl)

            subtitle_lbl = QLabel("AI Movie Dubbing Studio", content)
            subtitle_lbl.setStyleSheet("font-size: 15px; color: #687386;")
            greeting_section.addWidget(subtitle_lbl)
            layout.addLayout(greeting_section)

            # ---- Quick Actions ----
            actions_row = QHBoxLayout()
            actions_row.setSpacing(12)

            quick_dub_btn = QPushButton("⚡  1-Click Basic Dub", content)
            quick_dub_btn.setProperty("primary", "true")
            quick_dub_btn.setFixedHeight(42)
            quick_dub_btn.setMinimumWidth(180)
            quick_dub_btn.clicked.connect(self._on_quick_dub)
            actions_row.addWidget(quick_dub_btn)

            new_btn = QPushButton("＋  New Project", content)
            new_btn.setFixedHeight(42)
            new_btn.setMinimumWidth(160)
            new_btn.clicked.connect(self.new_project_requested)
            actions_row.addWidget(new_btn)

            open_btn = QPushButton("📂  Open Project", content)
            open_btn.setFixedHeight(42)
            open_btn.setMinimumWidth(160)
            open_btn.clicked.connect(self.open_project_requested)
            actions_row.addWidget(open_btn)

            import_btn = QPushButton("🎬  Import Movie", content)
            import_btn.setFixedHeight(42)
            import_btn.setMinimumWidth(160)
            import_btn.clicked.connect(self.open_project_requested)
            actions_row.addWidget(import_btn)

            actions_row.addStretch()
            layout.addLayout(actions_row)

        def _on_quick_dub(self) -> None:
            from aidub.ui.dialogs.quick_dub_dialog import QuickDubDialog  # noqa: PLC0415
            QuickDubDialog(self).exec()

            # ---- Recent Projects ----
            layout.addWidget(self._section_label("RECENT PROJECTS", content))

            grid = QGridLayout()
            grid.setSpacing(12)
            for i, (pid, name, lang, status, pct) in enumerate(self._RECENT_PROJECTS):
                card = _ProjectCard(pid, name, lang, status, pct, content)
                card.clicked.connect(self.project_opened)
                grid.addWidget(card, i // 3, i % 3)
            layout.addLayout(grid)

            # ---- Current Jobs ----
            layout.addWidget(self._section_label("CURRENT JOBS", content))

            jobs_col = QVBoxLayout()
            jobs_col.setSpacing(8)
            for title, stage, pct in self._ACTIVE_JOBS:
                jobs_col.addWidget(_JobRow(title, stage, pct, content))
            layout.addLayout(jobs_col)

            # ---- System Status ----
            layout.addWidget(self._section_label("SYSTEM", content))
            sys_row = QHBoxLayout()
            sys_row.setSpacing(12)
            sys_row.addWidget(self._sys_card("🖥  GPU", "RTX 4070   43%", "VRAM  6.8 / 12 GB", content))
            sys_row.addWidget(self._sys_card("💾  RAM", "18.2 / 32 GB", "CPU  12%", content))
            sys_row.addWidget(self._sys_card("🤖  Models", "4 loaded", "Whisper • Voice • Face", content))
            sys_row.addWidget(self._sys_card("💿  Storage", "310 GB free", "Exports: 328 GB", content))
            sys_row.addStretch()
            layout.addLayout(sys_row)

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll)

            # Refresh greeting every minute
            timer = QTimer(self)
            timer.timeout.connect(
                lambda: self._greeting_lbl.setText(_greeting())
            )
            timer.start(60_000)

        @staticmethod
        def _section_label(text: str, parent: _W) -> QLabel:
            lbl = QLabel(text, parent)
            lbl.setObjectName("SectionLabel")
            return lbl

        @staticmethod
        def _sys_card(title: str, line1: str, line2: str, parent: _W) -> QFrame:
            card = QFrame(parent)
            card.setObjectName("Card")
            card.setFixedSize(190, 80)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(12, 10, 12, 10)
            lay.setSpacing(3)
            t = QLabel(title, card)
            t.setStyleSheet("font-size: 12px; font-weight: 700; color: #A9B2C3;")
            lay.addWidget(t)
            l1 = QLabel(line1, card)
            l1.setStyleSheet("font-size: 13px; font-weight: 600; color: #F7F9FC;")
            lay.addWidget(l1)
            l2 = QLabel(line2, card)
            l2.setStyleSheet("font-size: 11px; color: #687386;")
            lay.addWidget(l2)
            return card


__all__ = ["DashboardScreen"]
