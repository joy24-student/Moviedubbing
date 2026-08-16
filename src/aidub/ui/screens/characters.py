"""
Character Studio screen.

3-pane layout:
  Left:   Character list with line counts and speaker IDs
  Center: Character profile (face, metadata, voice parameters)
  Right:  Voice panel with waveform comparison and scores
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QScrollArea,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


_CHARACTERS = [
    ("Tony",      "SPK_003", 312, 42.0,  "#4F8CFF"),
    ("Pepper",    "SPK_007", 174, 18.5,  "#EC4899"),
    ("Steve",     "SPK_001", 201, 28.2,  "#22C55E"),
    ("Nick",      "SPK_009",  88, 11.4,  "#F59E0B"),
    ("Natasha",   "SPK_005", 142, 21.8,  "#22D3EE"),
    ("Bruce",     "SPK_006",  76,  9.3,  "#A855F7"),
    ("Unknown 01","SPK_010",  18,  2.1,  "#687386"),
    ("Unknown 02","SPK_011",   7,  0.8,  "#687386"),
]

if _QT:

    class _CharCard(QFrame):  # type: ignore[misc]
        clicked = Signal(int)

        def __init__(self, idx: int, name: str, spk: str, lines: int,
                     screen_time: float, color: str, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._idx = idx
            self._selected = False
            self._color = color
            self.setObjectName("CharCard")
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setStyleSheet(
                f"QFrame#CharCard{{background:#161D28;border-left:3px solid {color};"
                f"border-top:none;border-right:1px solid #283241;border-bottom:1px solid #283241;"
                f"border-radius:0;}}"
                "QFrame#CharCard:hover{background:#1C2431;}"
            )

            lay = QHBoxLayout(self)
            lay.setContentsMargins(12, 10, 12, 10)
            lay.setSpacing(8)

            icon = QLabel("👤" if not name.startswith("Unknown") else "❓", self)
            icon.setStyleSheet(f"font-size:20px;color:{color};")
            lay.addWidget(icon)

            info = QVBoxLayout()
            name_lbl = QLabel(name, self)
            name_lbl.setStyleSheet(f"font-size:13px;font-weight:700;color:{'#F7F9FC' if not name.startswith('Unknown') else '#687386'};")
            info.addWidget(name_lbl)
            spk_lbl = QLabel(f"{spk}  ·  {screen_time:.0f}m", self)
            spk_lbl.setStyleSheet("font-size:11px;color:#687386;")
            info.addWidget(spk_lbl)
            lay.addLayout(info)
            lay.addStretch()

            lines_lbl = QLabel(str(lines), self)
            lines_lbl.setStyleSheet("font-size:14px;font-weight:700;color:#A9B2C3;")
            lay.addWidget(lines_lbl)

        def set_selected(self, sel: bool) -> None:
            self._selected = sel
            if sel:
                self.setStyleSheet(
                    f"QFrame#CharCard{{background:#1E3A5F;border-left:3px solid {self._color};"
                    f"border-top:none;border-right:1px solid #4F8CFF;border-bottom:1px solid #4F8CFF;"
                    f"border-radius:0;}}"
                )
            else:
                self.setStyleSheet(
                    f"QFrame#CharCard{{background:#161D28;border-left:3px solid {self._color};"
                    f"border-top:none;border-right:1px solid #283241;border-bottom:1px solid #283241;"
                    f"border-radius:0;}}"
                    "QFrame#CharCard:hover{background:#1C2431;}"
                )

        def mousePressEvent(self, _event: object) -> None:  # noqa: N802
            self.clicked.emit(self._idx)

    class _ProfilePanel(QScrollArea):  # type: ignore[misc]
        """Center character profile panel."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setWidgetResizable(True)
            self.setFrameShape(QFrame.Shape.NoFrame)
            self.setStyleSheet("background:#0D1118;")

            self._content = QWidget()
            self._content.setStyleSheet("background:#0D1118;")
            self._layout = QVBoxLayout(self._content)
            self._layout.setContentsMargins(24, 20, 24, 20)
            self._layout.setSpacing(16)
            self.setWidget(self._content)
            self._build_tony()

        def _build_tony(self) -> None:
            # Face placeholder
            face_frame = QFrame(self._content)
            face_frame.setFixedSize(110, 110)
            face_frame.setStyleSheet(
                "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #1C2431,stop:1 #0D1118);"
                "border:2px solid #4F8CFF;border-radius:55px;"
            )
            face_lay = QHBoxLayout(face_frame)
            face_ico = QLabel("👤", face_frame)
            face_ico.setStyleSheet("font-size:52px;background:transparent;border:none;")
            face_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            face_lay.addWidget(face_ico)
            self._layout.addWidget(face_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            name_lbl = QLabel("Tony Stark", self._content)
            name_lbl.setObjectName("ScreenTitle")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(name_lbl)

            fields = [
                ("Speaker ID", "SPK_003"),
                ("Screen Time", "42m 18s"),
                ("Voice Profile", "AI Voice #04"),
                ("Primary Language", "English"),
                ("Voice Style", "Confident, Sarcastic"),
                ("Accent", "American"),
                ("Age Style", "Adult (40s)"),
                ("Translation Style", "Casual / Assertive"),
            ]
            grid = QGridLayout()
            grid.setSpacing(8)
            for i, (k, v) in enumerate(fields):
                k_lbl = QLabel(k + ":", self._content)
                k_lbl.setObjectName("MetaLabel")
                v_lbl = QLabel(v, self._content)
                v_lbl.setObjectName("ValueLabel")
                grid.addWidget(k_lbl, i, 0)
                grid.addWidget(v_lbl, i, 1)
            self._layout.addLayout(grid)

            # Buttons
            btns = QHBoxLayout()
            btns.setSpacing(8)

            merge_b = QPushButton("Merge Speaker", self._content)
            merge_b.setFixedHeight(32)
            merge_b.clicked.connect(self._on_merge)
            btns.addWidget(merge_b)

            split_b = QPushButton("Split Speaker", self._content)
            split_b.setFixedHeight(32)
            split_b.clicked.connect(self._on_split)
            btns.addWidget(split_b)

            assign_v_b = QPushButton("Assign Voice", self._content)
            assign_v_b.setFixedHeight(32)
            assign_v_b.setProperty("accent", "ai")
            assign_v_b.clicked.connect(self._on_assign_voice)
            btns.addWidget(assign_v_b)

            btns.addStretch()
            self._layout.addLayout(btns)

        def _on_merge(self) -> None:
            from aidub.ui.dialogs.character_dialogs import MergeSpeakerDialog  # noqa: PLC0415
            MergeSpeakerDialog(self).exec()

        def _on_split(self) -> None:
            from aidub.ui.dialogs.character_dialogs import SplitSpeakerDialog  # noqa: PLC0415
            SplitSpeakerDialog(self).exec()

        def _on_assign_voice(self) -> None:
            from aidub.ui.dialogs.character_dialogs import AssignVoiceDialog  # noqa: PLC0415
            AssignVoiceDialog(self).exec()

            # Glossary / notes
            notes_lbl = QLabel("NOTES", self._content)
            notes_lbl.setObjectName("SectionLabel")
            self._layout.addWidget(notes_lbl)
            from PySide6.QtWidgets import QTextEdit  # noqa: PLC0415
            notes = QTextEdit(self._content)
            notes.setPlainText("Signature sarcasm should be preserved in all translations.\n"
                               "Avoid overly formal register in Bengali output.\n"
                               "Iron Man suit references: 'JARVIS' → 'জারভিস' (transliterate).")
            notes.setMaximumHeight(100)
            self._layout.addWidget(notes)
            self._layout.addStretch()

    class _VoicePanel(QWidget):  # type: ignore[misc]
        """Right voice preview and scores panel."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setStyleSheet("background:#161D28;border-left:1px solid #283241;")
            lay = QVBoxLayout(self)
            lay.setContentsMargins(16, 20, 16, 16)
            lay.setSpacing(12)

            title = QLabel("VOICE", self)
            title.setObjectName("SectionLabel")
            lay.addWidget(title)

            # Waveforms
            from aidub.ui.widgets.common import WaveformWidget  # noqa: PLC0415
            for label, color in [("Original", "#22D3EE"), ("Bengali Dub", "#4F8CFF")]:
                row_lay = QVBoxLayout()
                lbl = QLabel(label, self)
                lbl.setStyleSheet(f"font-size:11px;font-weight:700;color:{color};")
                row_lay.addWidget(lbl)
                wf = WaveformWidget(color=color, parent=self)
                wf.setFixedHeight(52)
                row_lay.addWidget(wf)
                pb = QPushButton("▶  Play", self)
                pb.setFixedHeight(28)
                row_lay.addWidget(pb)
                lay.addLayout(row_lay)

            # Scores
            scores_lbl = QLabel("SCORES", self)
            scores_lbl.setObjectName("SectionLabel")
            lay.addWidget(scores_lbl)

            scores = [("Voice Similarity", 96), ("Pitch Match", 92),
                      ("Energy Match", 89), ("Emotion Match", 94)]
            for sc_name, sc_val in scores:
                row = QHBoxLayout()
                n_lbl = QLabel(sc_name, self)
                n_lbl.setStyleSheet("font-size:12px;color:#A9B2C3;")
                row.addWidget(n_lbl)
                row.addStretch()
                color = "#22C55E" if sc_val >= 90 else "#F59E0B"
                v_lbl = QLabel(f"{sc_val}%", self)
                v_lbl.setStyleSheet(f"font-size:13px;font-weight:700;color:{color};")
                row.addWidget(v_lbl)
                lay.addLayout(row)

            # Action buttons
            lay.addSpacing(8)
            for label, accent in [("Preview", ""), ("Change Voice", "ai")]:
                btn = QPushButton(label, self)
                btn.setFixedHeight(34)
                if accent:
                    btn.setProperty("accent", accent)
                lay.addWidget(btn)

            lay.addStretch()

    class CharacterStudioScreen(QWidget):  # type: ignore[misc]
        """Character Studio — 3-pane character management."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._char_cards: list[_CharCard] = []
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            # Top bar
            topbar = QFrame(self)
            topbar.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;")
            topbar.setFixedHeight(48)
            tb = QHBoxLayout(topbar)
            tb.setContentsMargins(16, 0, 16, 0)
            title = QLabel("Character Studio", self)
            title.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(title)
            tb.addStretch()
            run_btn = QPushButton("🧠  Run Character Analysis", self)
            run_btn.setProperty("primary", "true")
            tb.addWidget(run_btn)
            root.addWidget(topbar)

            splitter = QSplitter(Qt.Orientation.Horizontal, self)

            # Left: Character list
            left = QWidget()
            left.setStyleSheet("background:#161D28;")
            left.setMinimumWidth(210)
            left.setMaximumWidth(280)
            left_layout = QVBoxLayout(left)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(0)

            hdr = QFrame(left)
            hdr.setStyleSheet("background:#1C2431;border-bottom:1px solid #283241;")
            hdr.setFixedHeight(38)
            hdr_lay = QHBoxLayout(hdr)
            hdr_lay.setContentsMargins(12, 0, 12, 0)
            hdr_lay.addWidget(QLabel("CHARACTERS", hdr))
            hdr_lay.addStretch()
            hdr_lay.addWidget(QLabel(f"{len(_CHARACTERS)}", hdr))
            left_layout.addWidget(hdr)

            for i, (name, spk, lines, st, color) in enumerate(_CHARACTERS):
                card = _CharCard(i, name, spk, lines, st, color, left)
                card.clicked.connect(self._select_char)
                left_layout.addWidget(card)
                self._char_cards.append(card)
            left_layout.addStretch()
            splitter.addWidget(left)

            # Center: Profile
            self._profile = _ProfilePanel()
            splitter.addWidget(self._profile)

            # Right: Voice
            self._voice_panel = _VoicePanel()
            self._voice_panel.setMinimumWidth(220)
            self._voice_panel.setMaximumWidth(300)
            splitter.addWidget(self._voice_panel)

            splitter.setSizes([240, 550, 250])
            root.addWidget(splitter, 1)

            # Select first
            self._select_char(0)

        def _select_char(self, idx: int) -> None:
            for i, card in enumerate(self._char_cards):
                card.set_selected(i == idx)


__all__ = ["CharacterStudioScreen"]
