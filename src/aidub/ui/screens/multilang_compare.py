"""
Side-by-Side Multi-Language Comparison screen (Master Spec Section 72).

Features:
- 4-column side-by-side localization dialogue comparison (English, Bengali, Hindi, Spanish)
- Synchronized timing & phrase verification matrix
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

    class MultiLangCompareScreen(QWidget):  # type: ignore[misc]
        """Side-by-Side Multi-Language Localization Workstation."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("MultiLangCompareScreen")
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            root.setSpacing(12)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("🌐  SIDE-BY-SIDE MULTI-LANGUAGE LOCALIZATION", self)
            title.setObjectName("ScreenTitle")
            hdr.addWidget(title)

            hdr.addStretch()

            sync_btn = QPushButton("🔄 Sync Timing All Languages", self)
            sync_btn.setProperty("primary", "true")
            hdr.addWidget(sync_btn)

            root.addLayout(hdr)

            # Comparison Table
            self.matrix = QTableWidget(0, 5, self)
            self.matrix.setHorizontalHeaderLabels([
                "Timecode & Speaker",
                "English Source",
                "Bengali Dub (Target)",
                "Hindi Dub",
                "Spanish Dub",
            ])
            self.matrix.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            for c in range(1, 5):
                self.matrix.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)

            self.matrix.setStyleSheet(
                "QTableWidget{background:#0D1118;gridline-color:#283241;border:1px solid #283241;}"
                "QHeaderView::section{background:#161D28;color:#A9B2C3;font-weight:700;padding:6px;border:none;}"
            )

            rows = [
                ("00:22:13.120\nTony", "I told you not to come here.", "আমি তোমাকে এখানে আসতে নিষেধ করেছিলাম।", "मैंने तुमसे कहा था यहाँ मत आओ।", "Te dije que no vinieras aquí."),
                ("00:22:16.800\nPepper", "I never asked for this.", "আমি কখনো এটা চাইনি।", "मैंने इसके लिए कभी नहीं कहा।", "Nunca pedí esto."),
                ("00:22:20.500\nSteve", "We need a plan before moving in.", "আমাদের ঢোকার আগে একটা পরিকল্পনা দরকার।", "अंदर जाने से पहले हमें एक योजना की ज़रूरत है।", "Necesitamos un plan antes de entrar."),
                ("00:22:24.900\nTony", "I always have a plan.", "আমার সবসময় পরিকল্পনা থাকে।", "मेरे पास हमेशा एक योजना होती है।", "Siempre tengo un plan."),
            ]

            self.matrix.setRowCount(len(rows))
            for r, (tc_spk, en, bn, hi, es) in enumerate(rows):
                self.matrix.setItem(r, 0, QTableWidgetItem(tc_spk))
                self.matrix.setItem(r, 1, QTableWidgetItem(en))
                self.matrix.setItem(r, 2, QTableWidgetItem(bn))
                self.matrix.setItem(r, 3, QTableWidgetItem(hi))
                self.matrix.setItem(r, 4, QTableWidgetItem(es))

            root.addWidget(self.matrix, 1)


__all__ = ["MultiLangCompareScreen"]
