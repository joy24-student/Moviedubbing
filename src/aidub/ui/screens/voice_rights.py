"""
Voice Rights & Consent Studio screen (Master Spec Section 83).

Features:
- Voice Profile Rights & Authorization Manager
- Character Voice, Authorization Status, Rights Owner, Allowed Languages, Expiry Date
- Actions: Add Evidence, Revoke Rights, Edit Authorization
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

    class VoiceRightsScreen(QWidget):  # type: ignore[misc]
        """Voice Rights & Legal Consent Workstation."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("VoiceRightsScreen")
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            root.setSpacing(12)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("📜  VOICE RIGHTS & CONSENT", self)
            title.setObjectName("ScreenTitle")
            hdr.addWidget(title)

            hdr.addStretch()

            add_btn = QPushButton("➕ Add Legal Consent Evidence", self)
            add_btn.setProperty("primary", "true")
            hdr.addWidget(add_btn)

            root.addLayout(hdr)

            # Info box
            info_box = QFrame(self)
            info_box.setStyleSheet(
                "QFrame{background:rgba(79,140,255,0.1);border:1px solid rgba(79,140,255,0.3);"
                "border-radius:8px;padding:10px 14px;}"
            )
            i_lay = QHBoxLayout(info_box)
            i_lay.addWidget(QLabel("🔒  Voice License Governance:", info_box))
            i_lbl = QLabel(
                "All synthesized voice clones require explicit legal authorization evidence before rendering commercial dubs.",
                info_box,
            )
            i_lbl.setStyleSheet("color:#A9B2C3;font-size:12px;")
            i_lay.addWidget(i_lbl, 1)
            root.addWidget(info_box)

            # Rights Table
            self.rights_table = QTableWidget(0, 5, self)
            self.rights_table.setHorizontalHeaderLabels([
                "Character / Voice Profile",
                "Authorization Status",
                "Rights Owner / Studio",
                "Allowed Dubbing Languages",
                "Expiration Date",
            ])
            self.rights_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.rights_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.rights_table.setStyleSheet(
                "QTableWidget{background:#0D1118;gridline-color:#283241;border:1px solid #283241;}"
                "QHeaderView::section{background:#161D28;color:#A9B2C3;font-weight:700;padding:6px;border:none;}"
            )

            records = [
                ("Tony Stark (Voice #04)", "✓ Authorized", "Marvel Entertainment LLC", "Bengali, Hindi, Spanish", "2027-08-20"),
                ("Pepper Potts (Voice #02)", "✓ Authorized", "Marvel Entertainment LLC", "Bengali, Hindi", "2027-08-20"),
                ("Steve Rogers (Voice #07)", "⚠ Expiring Soon", "Disney Localization Division", "Bengali, French", "2026-09-01"),
                ("Narrator (Studio AI #01)", "✓ Authorized (Royalty Free)", "Internal Studio License", "All Languages", "Perpetual"),
            ]

            self.rights_table.setRowCount(len(records))
            for r, (char, status, owner, langs, exp) in enumerate(records):
                self.rights_table.setItem(r, 0, QTableWidgetItem(char))
                s_item = QTableWidgetItem(status)
                if "Authorized" in status:
                    s_item.setForeground(Qt.GlobalColor.green)
                else:
                    s_item.setForeground(Qt.GlobalColor.yellow)
                self.rights_table.setItem(r, 1, s_item)
                self.rights_table.setItem(r, 2, QTableWidgetItem(owner))
                self.rights_table.setItem(r, 3, QTableWidgetItem(langs))
                self.rights_table.setItem(r, 4, QTableWidgetItem(exp))

            root.addWidget(self.rights_table, 1)


__all__ = ["VoiceRightsScreen"]
