"""
Translation Studio screen.

3-pane layout:
  Left: Scene list
  Center: Dialogue translation editor with per-line approve/reject/regenerate
  Right: AI Assistant chat panel
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMenu,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSplitter,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


_DEMO_LINES = [
    {
        "id": "utt_001",
        "char": "Tony",
        "ts": "00:22:13.120",
        "en": "I told you not to come here.",
        "bn": "আমি তোমাকে এখানে আসতে নিষেধ করেছিলাম।",
        "src_dur": 2.82,
        "tgt_dur": 2.96,
        "score": 97,
        "status": "approved",
    },
    {
        "id": "utt_002",
        "char": "Pepper",
        "ts": "00:22:16.400",
        "en": "You never listen to anyone.",
        "bn": "তুমি কখনো কারো কথা শোনো না।",
        "src_dur": 2.14,
        "tgt_dur": 2.08,
        "score": 94,
        "status": "ai_generated",
    },
    {
        "id": "utt_003",
        "char": "Tony",
        "ts": "00:22:19.200",
        "en": "That's what makes me good at what I do.",
        "bn": "এটাই আমাকে এই কাজে দক্ষ করে তোলে।",
        "src_dur": 2.60,
        "tgt_dur": 2.88,
        "score": 91,
        "status": "needs_review",
    },
    {
        "id": "utt_004",
        "char": "Steve",
        "ts": "00:22:22.800",
        "en": "We don't have time for this.",
        "bn": "আমাদের এর জন্য সময় নেই।",
        "src_dur": 1.82,
        "tgt_dur": 1.64,
        "score": 98,
        "status": "locked",
    },
    {
        "id": "utt_005",
        "char": "Tony",
        "ts": "00:22:25.000",
        "en": "Make time.",
        "bn": "সময় বের করো।",
        "src_dur": 0.82,
        "tgt_dur": 0.74,
        "score": 99,
        "status": "approved",
    },
    {
        "id": "utt_006",
        "char": "Pepper",
        "ts": "00:22:27.100",
        "en": "I never asked for this mission.",
        "bn": "আমি কখনো এই মিশনের জন্য অনুরোধ করিনি।",
        "src_dur": 2.40,
        "tgt_dur": 2.68,
        "score": 89,
        "status": "needs_review",
    },
]

_STATUS_COLORS = {
    "approved": ("#22C55E", "Approved"),
    "locked": ("#4F8CFF", "🔒 Locked"),
    "ai_generated": ("#A855F7", "AI Generated"),
    "needs_review": ("#F59E0B", "Needs Review"),
    "rejected": ("#EF4444", "Rejected"),
}

_CHAR_COLORS = {
    "Tony": "#4F8CFF",
    "Pepper": "#EC4899",
    "Steve": "#22C55E",
    "Narrator": "#F59E0B",
}

if _QT:

    class _DialogueRow(QFrame):  # type: ignore[misc]
        """Single dialogue translation row."""

        approved = Signal(str)
        rejected = Signal(str)
        regenerate = Signal(str)

        def __init__(self, data: dict, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._data = data
            self._build()

        def _build(self) -> None:
            d = self._data
            char_color = _CHAR_COLORS.get(d["char"], "#A9B2C3")
            status_color, status_text = _STATUS_COLORS.get(d["status"], ("#687386", d["status"]))

            self.setObjectName("DialogueRow")
            bg = "#1C2431" if d["status"] == "approved" else "#161D28"
            self.setStyleSheet(
                f"QFrame#DialogueRow{{background:{bg};border:1px solid #283241;"
                f"border-left:3px solid {char_color};border-radius:8px;}}"
                "QFrame#DialogueRow:hover{border-color:#34415A;}"
            )

            layout = QVBoxLayout(self)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(8)

            # Header row
            hdr = QHBoxLayout()
            char_lbl = QLabel(d["char"], self)
            char_lbl.setStyleSheet(
                f"font-size: 13px; font-weight: 700; color: {char_color};"
            )
            hdr.addWidget(char_lbl)
            ts_lbl = QLabel(d["ts"], self)
            ts_lbl.setStyleSheet("font-size: 11px; color: #687386;")
            hdr.addWidget(ts_lbl)
            hdr.addStretch()
            status_lbl = QLabel(status_text, self)
            status_lbl.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: {status_color};"
            )
            hdr.addWidget(status_lbl)
            layout.addLayout(hdr)

            # Original text (EN)
            lang_label = QLabel("EN", self)
            lang_label.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #687386; "
                "background: #283241; border-radius: 3px; padding: 1px 5px;"
            )
            en_lbl = QLabel(d["en"], self)
            en_lbl.setStyleSheet("font-size: 13px; color: #A9B2C3;")
            en_lbl.setWordWrap(True)
            en_row = QHBoxLayout()
            en_row.addWidget(lang_label, 0)
            en_row.addWidget(en_lbl, 1)
            layout.addLayout(en_row)

            # Translation (BN)
            bn_label = QLabel("BN", self)
            bn_label.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #A855F7; "
                "background: rgba(168,85,247,0.15); border-radius: 3px; padding: 1px 5px;"
            )
            self._bn_edit = QTextEdit(self)
            self._bn_edit.setPlainText(d["bn"])
            self._bn_edit.setMaximumHeight(60)
            self._bn_edit.setStyleSheet(
                "QTextEdit{background:transparent;border:none;color:#F7F9FC;"
                "font-size:14px;padding:0;}"
            )
            bn_row = QHBoxLayout()
            bn_row.setAlignment(Qt.AlignmentFlag.AlignTop)
            bn_row.addWidget(bn_label, 0, Qt.AlignmentFlag.AlignTop)
            bn_row.addWidget(self._bn_edit, 1)
            layout.addLayout(bn_row)

            # Timing + score
            timing_row = QHBoxLayout()
            diff = d["tgt_dur"] - d["src_dur"]
            diff_pct = (diff / d["src_dur"]) * 100 if d["src_dur"] > 0 else 0
            timing_lbl = QLabel(
                f"Original {d['src_dur']:.2f}s → Target {d['tgt_dur']:.2f}s"
                f"  Δ {diff_pct:+.1f}%",
                self,
            )
            timing_lbl.setStyleSheet(
                f"font-size: 11px; color: {'#F59E0B' if abs(diff_pct) > 10 else '#687386'};"
            )
            timing_row.addWidget(timing_lbl)
            timing_row.addStretch()
            score_lbl = QLabel(f"Score  {d['score']}%", self)
            sc_color = "#22C55E" if d["score"] >= 90 else "#F59E0B" if d["score"] >= 75 else "#EF4444"
            score_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {sc_color};")
            timing_row.addWidget(score_lbl)
            layout.addLayout(timing_row)

            # Action buttons
            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)

            approve_btn = QPushButton("✓ Approve", self)
            approve_btn.setProperty("accent", "success")
            approve_btn.setFixedHeight(28)
            approve_btn.clicked.connect(lambda: self.approved.emit(d["id"]))
            btn_row.addWidget(approve_btn)

            regen_btn = QPushButton("↺ Regenerate", self)
            regen_btn.setFixedHeight(28)
            regen_btn.clicked.connect(lambda: self.regenerate.emit(d["id"]))
            btn_row.addWidget(regen_btn)

            alt_btn = QPushButton("≡ Alternatives", self)
            alt_btn.setFixedHeight(28)
            alt_btn.clicked.connect(self._show_alternatives)
            btn_row.addWidget(alt_btn)

            btn_row.addStretch()

            ai_btn = QPushButton("🤖 AI Fix", self)
            ai_btn.setProperty("accent", "ai")
            ai_btn.setFixedHeight(28)
            btn_row.addWidget(ai_btn)

            layout.addLayout(btn_row)

        def _show_alternatives(self) -> None:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton  # noqa: PLC0415
            dlg = QDialog(self)
            dlg.setWindowTitle("Alternative Translations (A/B/C)")
            dlg.resize(460, 320)
            dlg.setStyleSheet("QDialog{background:#161D28;} QLabel{color:#F7F9FC;}")
            lay = QVBoxLayout(dlg)
            lay.addWidget(QLabel("CHOOSE TRANSLATION ALTERNATIVE:", dlg))

            alts = [
                ("Alternative A", "আমি তোমাকে এখানে আসতে মানা করেছিলাম।", "2.72s", "96%"),
                ("Alternative B ⭐", "আমি বলেছিলাম, এখানে এসো না।", "2.51s", "99%"),
                ("Alternative C", "আমি তো তোমাকে এখানে আসতে নিষেধ করেছিলাম।", "3.18s", "88%"),
            ]
            for label, text, dur, score in alts:
                card = QFrame(dlg)
                card.setStyleSheet("QFrame{background:#0D1118;border:1px solid #283241;border-radius:8px;padding:8px;}")
                c_lay = QVBoxLayout(card)
                h = QHBoxLayout()
                h.addWidget(QLabel(label, card))
                h.addStretch()
                h.addWidget(QLabel(f"Dur: {dur}  Score: {score}", card))
                c_lay.addLayout(h)
                t_lbl = QLabel(text, card)
                t_lbl.setStyleSheet("font-size:13px;color:#22D3EE;")
                c_lay.addWidget(t_lbl)
                use_btn = QPushButton("Use This Translation", card)
                use_btn.setFixedHeight(26)
                use_btn.clicked.connect(lambda _=False, t=text: (self._bn_edit.setText(t), dlg.accept()))
                c_lay.addWidget(use_btn)
                lay.addWidget(card)
            dlg.exec()

    class TranslationScreen(QWidget):  # type: ignore[misc]
        """Translation Studio — professional 3-pane translation editor."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            # Top bar
            topbar = QFrame(self)
            topbar.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;")
            topbar.setFixedHeight(48)
            tb_layout = QHBoxLayout(topbar)
            tb_layout.setContentsMargins(16, 0, 16, 0)
            tb_layout.setSpacing(12)

            title_lbl = QLabel("Translation Studio", self)
            title_lbl.setObjectName("ScreenTitle")
            title_lbl.setStyleSheet("font-size: 18px; font-weight: 700;")
            tb_layout.addWidget(title_lbl)
            tb_layout.addStretch()

            lang_lbl = QLabel("Target Language:", self)
            lang_lbl.setStyleSheet("color: #687386; font-size: 12px;")
            tb_layout.addWidget(lang_lbl)
            lang_combo = QComboBox(self)
            lang_combo.addItems(["বাংলা (Bengali)", "हिंदी (Hindi)", "Español (Spanish)"])
            lang_combo.setFixedWidth(180)
            tb_layout.addWidget(lang_combo)

            batch_btn = QPushButton("⚡ Translate All", self)
            batch_btn.setProperty("primary", "true")
            tb_layout.addWidget(batch_btn)
            root.addWidget(topbar)

            # 3-pane splitter
            splitter = QSplitter(Qt.Orientation.Horizontal, self)

            # Left: Scene list
            scene_panel = QWidget()
            scene_panel.setStyleSheet("background:#161D28;")
            scene_panel.setMinimumWidth(160)
            scene_panel.setMaximumWidth(220)
            sp_layout = QVBoxLayout(scene_panel)
            sp_layout.setContentsMargins(0, 0, 0, 0)
            sp_layout.setSpacing(0)

            sl_header = QLabel("SCENES", scene_panel)
            sl_header.setObjectName("SectionLabel")
            sl_header.setContentsMargins(12, 10, 12, 8)
            sp_layout.addWidget(sl_header)

            scene_list = QListWidget(scene_panel)
            scene_list.setObjectName("NavList")
            scene_list.setStyleSheet(
                "QListWidget{background:#161D28;border:none;border-right:1px solid #283241;}"
                "QListWidget::item{padding:10px 14px;border-radius:0;margin:0;}"
                "QListWidget::item:selected{background:#1E3A5F;color:#F7F9FC;border:none;}"
            )
            for i in range(22, 35):
                item = QListWidgetItem(f"Scene {i:03d}")
                scene_list.addItem(item)
            scene_list.setCurrentRow(2)
            sp_layout.addWidget(scene_list, 1)
            splitter.addWidget(scene_panel)

            # Center: Translation editor
            center_panel = QWidget()
            cp_layout = QVBoxLayout(center_panel)
            cp_layout.setContentsMargins(0, 0, 0, 0)
            cp_layout.setSpacing(0)

            scroll = QScrollArea(center_panel)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            lines_container = QWidget()
            lines_container.setStyleSheet("background: #0D1118;")
            lines_layout = QVBoxLayout(lines_container)
            lines_layout.setContentsMargins(16, 16, 16, 16)
            lines_layout.setSpacing(10)

            for line_data in _DEMO_LINES:
                row = _DialogueRow(line_data, lines_container)
                lines_layout.addWidget(row)
            lines_layout.addStretch()

            scroll.setWidget(lines_container)
            cp_layout.addWidget(scroll)
            splitter.addWidget(center_panel)

            # Right: AI Assistant
            ai_panel = QWidget()
            ai_panel.setStyleSheet("background:#161D28;border-left:1px solid #283241;")
            ai_panel.setMinimumWidth(220)
            ai_panel.setMaximumWidth(300)
            ai_layout = QVBoxLayout(ai_panel)
            ai_layout.setContentsMargins(14, 14, 14, 14)
            ai_layout.setSpacing(10)

            ai_title = QLabel("🤖  AI Assistant", ai_panel)
            ai_title.setObjectName("PanelTitle")
            ai_layout.addWidget(ai_title)

            ai_history = QScrollArea(ai_panel)
            ai_history.setWidgetResizable(True)
            ai_history.setFrameShape(QFrame.Shape.NoFrame)
            hist_content = QWidget()
            hist_layout = QVBoxLayout(hist_content)
            hist_layout.setContentsMargins(0, 0, 0, 0)
            hist_layout.setSpacing(8)

            sample_prompts = [
                ("You", "Make Tony's dialogue more sarcastic but under 2.8 seconds."),
                ("AI", "Done. Adjusted 3 lines with more assertive tone while keeping timing within bounds."),
            ]
            for sender, msg in sample_prompts:
                bubble = QFrame(hist_content)
                is_user = sender == "You"
                bubble.setStyleSheet(
                    f"QFrame{{background:{'#1E3A5F' if is_user else '#1C2431'};"
                    f"border-radius:8px;border:1px solid #283241;}}"
                )
                b_lay = QVBoxLayout(bubble)
                b_lay.setContentsMargins(10, 8, 10, 8)
                s_lbl = QLabel(sender, bubble)
                s_lbl.setStyleSheet(f"font-size:11px;font-weight:700;color:{'#4F8CFF' if is_user else '#A855F7'};")
                b_lay.addWidget(s_lbl)
                m_lbl = QLabel(msg, bubble)
                m_lbl.setStyleSheet("font-size:12px;color:#A9B2C3;")
                m_lbl.setWordWrap(True)
                b_lay.addWidget(m_lbl)
                hist_layout.addWidget(bubble)
            hist_layout.addStretch()
            ai_history.setWidget(hist_content)
            ai_layout.addWidget(ai_history, 1)

            ai_input = QTextEdit(ai_panel)
            ai_input.setPlaceholderText("Ask about this scene…")
            ai_input.setMaximumHeight(80)
            ai_layout.addWidget(ai_input)

            send_btn = QPushButton("Send  ↵", ai_panel)
            send_btn.setProperty("accent", "ai")
            ai_layout.addWidget(send_btn)

            # Quick commands
            quick_lbl = QLabel("QUICK COMMANDS", ai_panel)
            quick_lbl.setObjectName("SectionLabel")
            ai_layout.addWidget(quick_lbl)

            for cmd in ["Improve scene", "Check consistency", "Shorten all", "Fix glossary"]:
                cb = QPushButton(cmd, ai_panel)
                cb.setFixedHeight(28)
                cb.setStyleSheet("font-size:11px;padding:3px 8px;")
                ai_layout.addWidget(cb)

            splitter.addWidget(ai_panel)
            splitter.setSizes([180, 600, 260])

            root.addWidget(splitter, 1)


__all__ = ["TranslationScreen"]
