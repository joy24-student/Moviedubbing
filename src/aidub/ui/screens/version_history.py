"""
Version History & Snapshot Manager screen (Master Spec Section 73).

Features:
- Version snapshot history table (Tag, Timestamp, Stage Description, Author, Size)
- Actions: Create Snapshot, Restore Version, Compare Snapshots, Duplicate Version
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPushButton,
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

    class VersionHistoryScreen(QWidget):  # type: ignore[misc]
        """Project Version History & Snapshot Workstation."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("VersionHistoryScreen")
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            root.setSpacing(12)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("🕒  VERSION HISTORY & SNAPSHOTS", self)
            title.setObjectName("ScreenTitle")
            hdr.addWidget(title)

            hdr.addStretch()

            snap_btn = QPushButton("📸 Create Named Snapshot", self)
            snap_btn.setProperty("primary", "true")
            hdr.addWidget(snap_btn)

            root.addLayout(hdr)

            # Control bar
            tbar = QFrame(self)
            tbar.setObjectName("Panel")
            t_lay = QHBoxLayout(tbar)
            t_lay.setContentsMargins(10, 8, 10, 8)
            t_lay.setSpacing(10)

            t_lay.addWidget(QPushButton("↺ Restore Version", tbar))
            t_lay.addWidget(QPushButton("🔍 Compare Snapshots", tbar))
            t_lay.addWidget(QPushButton("📋 Duplicate Version", tbar))
            t_lay.addStretch()

            root.addWidget(tbar)

            # Table
            self.ver_table = QTableWidget(0, 5, self)
            self.ver_table.setHorizontalHeaderLabels([
                "Version Tag",
                "Created Timestamp",
                "Stage Description / Milestone",
                "Author",
                "Snapshot Size",
            ])
            self.ver_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.ver_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.ver_table.setStyleSheet(
                "QTableWidget{background:#0D1118;gridline-color:#283241;border:1px solid #283241;}"
                "QHeaderView::section{background:#161D28;color:#A9B2C3;font-weight:700;padding:6px;border:none;}"
            )

            snapshots = [
                ("v18 (Current Head)", "2026-08-16 01:24:10", "Voice timing fine-tuning & Lip-Sync pass", "Lead Editor", "1.4 GB"),
                ("v17", "2026-08-15 22:14:02", "Voice corrections & ElevenLabs multi-take selection", "AI Dubbing Bot", "1.2 GB"),
                ("v16", "2026-08-15 18:45:11", "Bengali Translation approved by Localization Manager", "Localization Lead", "840 MB"),
                ("v15", "2026-08-15 14:10:00", "Initial ASR Transcript & Character Diarization", "System Engine", "620 MB"),
                ("v01 (Original)", "2026-08-15 10:00:00", "Movie project creation", "Lead Editor", "120 MB"),
            ]

            self.ver_table.setRowCount(len(snapshots))
            for r, (tag, ts, desc, author, sz) in enumerate(snapshots):
                t_item = QTableWidgetItem(tag)
                if "Current" in tag:
                    t_item.setForeground(Qt.GlobalColor.green)
                self.ver_table.setItem(r, 0, t_item)
                self.ver_table.setItem(r, 1, QTableWidgetItem(ts))
                self.ver_table.setItem(r, 2, QTableWidgetItem(desc))
                self.ver_table.setItem(r, 3, QTableWidgetItem(author))
                self.ver_table.setItem(r, 4, QTableWidgetItem(sz))

            root.addWidget(self.ver_table, 1)


__all__ = ["VersionHistoryScreen"]
