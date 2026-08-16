"""
Pronunciation Studio screen (Master Spec Section 18).

Features:
- Term phonetic dictionary table (Term, Target, Phonetic IPA, Scope, Category)
- Category filters (Character Names, Places, Brands, Technical, Fantasy, Foreign, Numbers)
- Actions: Add, Edit, Delete, TTS Audio Preview, Import/Export dictionary
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
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

    class PronunciationStudioScreen(QWidget):  # type: ignore[misc]
        """Phonetic pronunciation dictionary editor workstation."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("PronunciationStudioScreen")
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            root.setSpacing(12)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("📖  PRONUNCIATION STUDIO", self)
            title.setObjectName("ScreenTitle")
            hdr.addWidget(title)

            hdr.addStretch()

            exp_btn = QPushButton("📥 Import Dictionary", self)
            hdr.addWidget(exp_btn)

            imp_btn = QPushButton("📤 Export Dictionary", self)
            hdr.addWidget(imp_btn)

            root.addLayout(hdr)

            # Control bar
            ctrl_bar = QFrame(self)
            ctrl_bar.setObjectName("Panel")
            ctrl_lay = QHBoxLayout(ctrl_bar)
            ctrl_lay.setContentsMargins(10, 8, 10, 8)
            ctrl_lay.setSpacing(10)

            add_btn = QPushButton("➕ Add Term", ctrl_bar)
            add_btn.setProperty("primary", "true")
            ctrl_lay.addWidget(add_btn)

            edit_btn = QPushButton("✏️ Edit Term", ctrl_bar)
            ctrl_lay.addWidget(edit_btn)

            del_btn = QPushButton("🗑️ Delete Term", ctrl_bar)
            del_btn.setProperty("accent", "danger")
            ctrl_lay.addWidget(del_btn)

            prev_btn = QPushButton("▶ Preview TTS Pronunciation", ctrl_bar)
            ctrl_lay.addWidget(prev_btn)

            ctrl_lay.addStretch()

            ctrl_lay.addWidget(QLabel("Filter Category:", ctrl_bar))
            cat_filter = QComboBox(ctrl_bar)
            cat_filter.addItems([
                "All Categories",
                "Character Names",
                "Places",
                "Brands",
                "Technical Terms",
                "Fantasy Words",
                "Foreign Words",
                "Numbers & Abbreviations",
            ])
            ctrl_lay.addWidget(cat_filter)

            root.addWidget(ctrl_bar)

            # Term dictionary table
            self.dict_table = QTableWidget(0, 5, self)
            self.dict_table.setHorizontalHeaderLabels([
                "Original Term",
                "Target Phonetic Spelling",
                "IPA Phonetic Representation",
                "Category",
                "Scope",
            ])
            self.dict_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.dict_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.dict_table.setStyleSheet(
                "QTableWidget{background:#0D1118;gridline-color:#283241;border:1px solid #283241;}"
                "QHeaderView::section{background:#161D28;color:#A9B2C3;font-weight:700;padding:6px;border:none;}"
            )

            sample_terms = [
                ("Wakanda", "ওয়াকান্ডা", "/wəˈkɑːndə/", "Place", "Project"),
                ("Tony Stark", "টনি স্টার্ক", "/ˈtoʊni stɑːrk/", "Character Name", "Global"),
                ("JARVIS", "জার্ভিস", "/ˈdʒɑːrvɪs/", "Technical Term", "Project"),
                ("Mjolnir", "মিয়োলনির", "/ˈmjɔːlnɪər/", "Fantasy Word", "Global"),
                ("Vibranium", "ভাইব্রেনিয়াম", "/vaɪˈbreɪniəm/", "Technical Term", "Project"),
            ]
            self.dict_table.setRowCount(len(sample_terms))
            for r, (term, tgt, ipa, cat, scope) in enumerate(sample_terms):
                self.dict_table.setItem(r, 0, QTableWidgetItem(term))
                self.dict_table.setItem(r, 1, QTableWidgetItem(tgt))
                self.dict_table.setItem(r, 2, QTableWidgetItem(ipa))
                self.dict_table.setItem(r, 3, QTableWidgetItem(cat))
                self.dict_table.setItem(r, 4, QTableWidgetItem(scope))

            root.addWidget(self.dict_table, 1)


__all__ = ["PronunciationStudioScreen"]
