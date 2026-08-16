"""
Scene Browser screen (Master Spec Section 17).

Features:
- Scene grid view (Scene #, Timecode range, Thumbnail, Characters, Lines, Quality %)
- Filter bar (All, Dialogue, Action, Close-up, Low Confidence, Lip Sync Required, QC Issues)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
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

    class SceneCard(QFrame):  # type: ignore[misc]
        """Individual Scene Grid Item."""

        def __init__(self, scene_id: str, tc: str, chars: str, lines: int, score: int, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("Panel")
            self.setMinimumSize(240, 180)
            self.setStyleSheet(
                "QFrame#Panel{background:#161D28;border:1px solid #283241;border-radius:10px;}"
                "QFrame#Panel:hover{border:1px solid #4F8CFF;}"
            )

            lay = QVBoxLayout(self)
            lay.setContentsMargins(10, 10, 10, 10)
            lay.setSpacing(6)

            # Header
            hdr = QHBoxLayout()
            s_lbl = QLabel(scene_id, self)
            s_lbl.setStyleSheet("font-size:14px;font-weight:700;color:#F7F9FC;")
            hdr.addWidget(s_lbl)
            hdr.addStretch()
            sc_color = "#22C55E" if score >= 90 else "#F59E0B" if score >= 75 else "#EF4444"
            sc_lbl = QLabel(f"Score {score}%", self)
            sc_lbl.setStyleSheet(f"font-size:11px;font-weight:700;color:{sc_color};")
            hdr.addWidget(sc_lbl)
            lay.addLayout(hdr)

            # Thumbnail placeholder
            thumb = QLabel("[ THUMBNAIL ]", self)
            thumb.setFixedHeight(80)
            thumb.setStyleSheet("background:#0D1118;border-radius:6px;color:#687386;")
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(thumb)

            # Timecode
            tc_lbl = QLabel(tc, self)
            tc_lbl.setStyleSheet("font-size:11px;color:#A9B2C3;font-family:'Cascadia Code';")
            lay.addWidget(tc_lbl)

            # Meta
            meta_lbl = QLabel(f"Characters: {chars} • {lines} lines", self)
            meta_lbl.setStyleSheet("font-size:11px;color:#687386;")
            lay.addWidget(meta_lbl)

    class SceneBrowserScreen(QWidget):  # type: ignore[misc]
        """Scene Browser workstation with filter bar."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("SceneBrowserScreen")
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            root.setSpacing(12)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("🎬  SCENE BROWSER", self)
            title.setObjectName("ScreenTitle")
            hdr.addWidget(title)

            hdr.addStretch()

            hdr.addWidget(QLabel("Filter Scene Type:", self))
            filter_cb = QComboBox(self)
            filter_cb.addItems([
                "All Scenes (173)",
                "Dialogue Scenes (142)",
                "Action Scenes (31)",
                "Close-up Shots (88)",
                "Low Confidence (3)",
                "Lip Sync Required (24)",
                "QC Issues (22)",
            ])
            hdr.addWidget(filter_cb)

            root.addLayout(hdr)

            # Grid scroll area
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)

            grid_widget = QWidget()
            grid_lay = QGridLayout(grid_widget)
            grid_lay.setContentsMargins(0, 0, 0, 0)
            grid_lay.setSpacing(12)

            sample_scenes = [
                ("Scene 001", "00:00:00 – 00:01:48", "Tony, Pepper", 17, 96),
                ("Scene 002", "00:01:48 – 00:04:12", "Steve, Nat", 24, 94),
                ("Scene 003", "00:04:12 – 00:06:55", "Thor, Loki", 31, 88),
                ("Scene 004", "00:06:55 – 00:09:30", "Tony, Bruce", 19, 92),
                ("Scene 005", "00:09:30 – 00:12:10", "Pepper, Happy", 12, 78),
                ("Scene 006", "00:12:10 – 00:15:40", "Steve, Tony", 28, 97),
                ("Scene 007", "00:15:40 – 00:18:22", "Nat, Clint", 15, 91),
                ("Scene 008", "00:18:22 – 00:22:14", "Wanda, Vision", 22, 95),
            ]

            cols = 4
            for i, (sid, tc, chars, lines, score) in enumerate(sample_scenes):
                card = SceneCard(sid, tc, chars, lines, score, grid_widget)
                grid_lay.addWidget(card, i // cols, i % cols)

            scroll.setWidget(grid_widget)
            root.addWidget(scroll, 1)


__all__ = ["SceneBrowserScreen"]
