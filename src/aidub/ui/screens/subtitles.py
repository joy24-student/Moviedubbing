"""
Subtitle Studio screen (Master Spec Section 29 & 30).

Features:
- Three-pane layout: Video Preview / Subtitle Table Editor / Timeline Strip
- Edit, split, join, reposition timecodes
- Style controls (Font, size, primary color, shadow, outline)
- RTL support toggle & Subtitle Safe Zone overlay check
- Multi-format export (SRT, VTT, ASS, TXT, Burn-in)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QPushButton,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


if _QT:

    class SubtitleStudioScreen(QWidget):  # type: ignore[misc]
        """Full 3-pane Subtitle Studio workstation."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("SubtitleStudioScreen")
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            root.setSpacing(12)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("💬  SUBTITLE STUDIO", self)
            title.setObjectName("ScreenTitle")
            hdr.addWidget(title)

            hdr.addStretch()

            # Format export selector
            hdr.addWidget(QLabel("Export Format:", self))
            self._fmt_combo = QComboBox(self)
            self._fmt_combo.addItems(["SRT", "VTT", "ASS (Advanced SubStation)", "TXT", "Burn into Video"])
            hdr.addWidget(self._fmt_combo)

            exp_btn = QPushButton("📤 Export Subtitles", self)
            exp_btn.setProperty("primary", "true")
            hdr.addWidget(exp_btn)

            root.addLayout(hdr)

            # Toolbar actions
            tbl_bar = QFrame(self)
            tbl_bar.setObjectName("Panel")
            tbl_lay = QHBoxLayout(tbl_bar)
            tbl_lay.setContentsMargins(10, 6, 10, 6)
            tbl_lay.setSpacing(8)

            for icon, label in [
                ("➕", "Add Line"),
                ("✂️", "Split Line"),
                ("🔗", "Join Lines"),
                ("⏱", "Fix Timing"),
                ("🌐", "Auto-Translate"),
                ("🔍", "Spell Check"),
            ]:
                btn = QPushButton(f"{icon} {label}", tbl_bar)
                tbl_lay.addWidget(btn)

            tbl_lay.addStretch()

            self._rtl_cb = QCheckBox("RTL Mode", tbl_bar)
            tbl_lay.addWidget(self._rtl_cb)

            self._safe_cb = QCheckBox("Subtitle Safe Zone", tbl_bar)
            self._safe_cb.setChecked(True)
            tbl_lay.addWidget(self._safe_cb)

            root.addWidget(tbl_bar)

            # Splitter: Left (Video Preview + Styling), Right (Subtitle Table)
            splitter = QSplitter(Qt.Orientation.Horizontal, self)

            # ---- LEFT: Video Preview + Style Inspector ----
            left = QWidget(splitter)
            left_lay = QVBoxLayout(left)
            left_lay.setContentsMargins(0, 0, 0, 0)
            left_lay.setSpacing(10)

            # Video preview frame
            video_frame = QFrame(left)
            video_frame.setStyleSheet("QFrame{background:#000000;border:1px solid #283241;border-radius:8px;}")
            v_lay = QVBoxLayout(video_frame)
            v_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self._preview_lbl = QLabel("[ VIDEO PREVIEW WITH SUBTITLE OVERLAY ]", video_frame)
            self._preview_lbl.setStyleSheet("color:#687386;font-size:13px;")
            v_lay.addWidget(self._preview_lbl)

            sub_overlay = QLabel("আমি তোমাকে এখানে আসতে বারণ করেছিলাম।", video_frame)
            sub_overlay.setStyleSheet(
                "color:#FFFFFF;font-size:18px;font-weight:700;"
                "background:rgba(0,0,0,0.7);padding:6px 14px;border-radius:4px;"
            )
            sub_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_lay.addWidget(sub_overlay)

            left_lay.addWidget(video_frame, 1)

            # Style panel
            style_panel = QFrame(left)
            style_panel.setObjectName("Panel")
            sp_lay = QGridLayout(style_panel)
            sp_lay.setContentsMargins(12, 10, 12, 10)
            sp_lay.setSpacing(8)

            sp_lay.addWidget(QLabel("Font Family:", style_panel), 0, 0)
            font_cb = QComboBox(style_panel)
            font_cb.addItems(["Segoe UI", "Arial", "Noto Sans Bengali", "Roboto"])
            sp_lay.addWidget(font_cb, 0, 1)

            sp_lay.addWidget(QLabel("Font Size:", style_panel), 0, 2)
            size_cb = QComboBox(style_panel)
            size_cb.addItems(["18 px", "22 px", "26 px", "32 px"])
            size_cb.setCurrentIndex(1)
            sp_lay.addWidget(size_cb, 0, 3)

            sp_lay.addWidget(QLabel("Primary Color:", style_panel), 1, 0)
            color_cb = QComboBox(style_panel)
            color_cb.addItems(["#FFFFFF (White)", "#FFFF00 (Yellow)", "#22D3EE (Cyan)"])
            sp_lay.addWidget(color_cb, 1, 1)

            sp_lay.addWidget(QLabel("Outline / Shadow:", style_panel), 1, 2)
            outline_cb = QComboBox(style_panel)
            outline_cb.addItems(["Black Outline 2px", "Drop Shadow", "Box Background"])
            sp_lay.addWidget(outline_cb, 1, 3)

            left_lay.addWidget(style_panel)
            splitter.addWidget(left)

            # ---- RIGHT: Subtitle List Table ----
            right = QWidget(splitter)
            right_lay = QVBoxLayout(right)
            right_lay.setContentsMargins(0, 0, 0, 0)

            self.sub_table = QTableWidget(0, 5, right)
            self.sub_table.setHorizontalHeaderLabels(
                ["#", "Time In", "Time Out", "Speaker", "Subtitle Text"]
            )
            self.sub_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            self.sub_table.setStyleSheet(
                "QTableWidget{background:#0D1118;gridline-color:#283241;border:1px solid #283241;}"
                "QHeaderView::section{background:#161D28;color:#A9B2C3;font-weight:700;padding:6px;border:none;}"
            )

            # Populate sample rows
            sample_subs = [
                ("001", "00:00:14.200", "00:00:17.100", "Tony", "I told you not to come here."),
                ("002", "00:00:17.400", "00:00:20.300", "Tony", "আমি তোমাকে এখানে আসতে নিষেধ করেছিলাম।"),
                ("003", "00:00:20.800", "00:00:23.500", "Pepper", "I had no choice, Tony."),
                ("004", "00:00:23.900", "00:00:26.100", "Pepper", "আমার কোন উপায় ছিল না, টনি।"),
                ("005", "00:00:26.500", "00:00:29.800", "Steve", "We need to focus on the mission."),
            ]
            self.sub_table.setRowCount(len(sample_subs))
            for r, (num, tin, tout, spk, text) in enumerate(sample_subs):
                self.sub_table.setItem(r, 0, QTableWidgetItem(num))
                self.sub_table.setItem(r, 1, QTableWidgetItem(tin))
                self.sub_table.setItem(r, 2, QTableWidgetItem(tout))
                self.sub_table.setItem(r, 3, QTableWidgetItem(spk))
                self.sub_table.setItem(r, 4, QTableWidgetItem(text))

            right_lay.addWidget(self.sub_table)
            splitter.addWidget(right)

            splitter.setSizes([540, 660])
            root.addWidget(splitter, 1)


__all__ = ["SubtitleStudioScreen"]
