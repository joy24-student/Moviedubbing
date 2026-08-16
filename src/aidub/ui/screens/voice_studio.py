"""
Voice Studio screen.

ElevenLabs + DAW style voice direction panel:
- Character/language header
- Reference audio waveform
- Voice selector + similarity score
- Parameter sliders (Pitch, Energy, Warmth, Roughness, Speed)
- Emotion + Intensity controls
- Takes list (multi-take system with ★ ratings)
- Original vs Dubbed waveform comparison
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QScrollArea,
        QSlider,
        QSplitter,
        QVBoxLayout,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


if _QT:

    def _param_row(label: str, value: int, parent: QWidget) -> tuple[QFrame, QSlider]:
        frame = QFrame(parent)
        frame.setStyleSheet("QFrame{background:transparent;border:none;}")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lbl = QLabel(label, frame)
        lbl.setFixedWidth(90)
        lbl.setStyleSheet("font-size: 12px; color: #A9B2C3;")
        slider = QSlider(Qt.Orientation.Horizontal, frame)
        slider.setRange(0, 100)
        slider.setValue(value)
        val_lbl = QLabel(str(value), frame)
        val_lbl.setFixedWidth(28)
        val_lbl.setStyleSheet("font-size: 12px; color: #687386;")
        slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
        lay.addWidget(lbl)
        lay.addWidget(slider, 1)
        lay.addWidget(val_lbl)
        return frame, slider

    class _TakeRow(QFrame):  # type: ignore[misc]
        selected = Signal(int)

        def __init__(self, take_num: int, score: int, is_active: bool, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._take_num = take_num
            bg = "#1E3A5F" if is_active else "#1C2431"
            self.setStyleSheet(
                f"QFrame{{background:{bg};border:1px solid "
                f"{'#4F8CFF' if is_active else '#283241'};border-radius:7px;}}"
            )
            self.setCursor(Qt.CursorShape.PointingHandCursor)

            lay = QHBoxLayout(self)
            lay.setContentsMargins(12, 8, 12, 8)
            lay.setSpacing(8)

            lbl = QLabel(f"Take {take_num}", self)
            lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
            lay.addWidget(lbl)

            if is_active:
                active_badge = QLabel("★ Active", self)
                active_badge.setStyleSheet("font-size: 11px; color: #F59E0B;")
                lay.addWidget(active_badge)

            lay.addStretch()

            score_lbl = QLabel(f"{score}%", self)
            sc_color = "#22C55E" if score >= 90 else "#F59E0B" if score >= 75 else "#EF4444"
            score_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sc_color};")
            lay.addWidget(score_lbl)

            play_btn = QPushButton("▶", self)
            play_btn.setFixedSize(28, 28)
            play_btn.setStyleSheet("QPushButton{background:#283241;border-radius:14px;border:none;font-size:12px;}"
                                   "QPushButton:hover{background:#4F8CFF;}")
            lay.addWidget(play_btn)

        def mousePressEvent(self, _event: object) -> None:  # noqa: N802
            self.selected.emit(self._take_num)

    class VoiceStudioScreen(QWidget):  # type: ignore[misc]
        """Voice Studio — character voice direction and generation."""

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
            tb = QHBoxLayout(topbar)
            tb.setContentsMargins(16, 0, 16, 0)
            tb.setSpacing(12)

            QLabel("Voice Studio", topbar).setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(QLabel("Voice Studio", topbar))
            tb.addStretch()

            char_combo = QComboBox(topbar)
            char_combo.addItems(["Tony", "Pepper", "Steve", "Narrator"])
            char_combo.setFixedWidth(130)
            tb.addWidget(QLabel("Character:", topbar))
            tb.addWidget(char_combo)

            lang_combo = QComboBox(topbar)
            lang_combo.addItems(["বাংলা (Bengali)", "हिंदी (Hindi)"])
            lang_combo.setFixedWidth(160)
            tb.addWidget(QLabel("Language:", topbar))
            tb.addWidget(lang_combo)
            root.addWidget(topbar)

            # Main content
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QHBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 20)
            layout.setSpacing(16)

            # ---- LEFT: Voice Profile Controls ----
            left = QFrame(content)
            left.setObjectName("Panel")
            left.setMinimumWidth(320)
            left.setMaximumWidth(380)
            left_layout = QVBoxLayout(left)
            left_layout.setContentsMargins(16, 16, 16, 16)
            left_layout.setSpacing(14)

            # Character header
            char_hdr = QHBoxLayout()
            char_icon = QLabel("👤", left)
            char_icon.setStyleSheet("font-size:36px;")
            char_hdr.addWidget(char_icon)
            char_info = QVBoxLayout()
            n = QLabel("Tony Stark — Bengali", left)
            n.setStyleSheet("font-size:15px;font-weight:700;")
            char_info.addWidget(n)
            sub = QLabel("AI Voice #04  ·  Similarity 96%", left)
            sub.setStyleSheet("font-size:12px;color:#687386;")
            char_info.addWidget(sub)
            char_hdr.addLayout(char_info)
            char_hdr.addStretch()
            left_layout.addLayout(char_hdr)

            # Section: Reference Audio
            ra_lbl = QLabel("REFERENCE AUDIO", left)
            ra_lbl.setObjectName("SectionLabel")
            left_layout.addWidget(ra_lbl)
            from aidub.ui.widgets.common import WaveformWidget  # noqa: PLC0415
            wf = WaveformWidget(color="#4F8CFF", parent=left)
            wf.setFixedHeight(56)
            left_layout.addWidget(wf)

            # Section: Parameters
            params_lbl = QLabel("VOICE PARAMETERS", left)
            params_lbl.setObjectName("SectionLabel")
            left_layout.addWidget(params_lbl)

            params = [
                ("Pitch", 52), ("Energy", 68), ("Warmth", 61), ("Roughness", 34), ("Speed ×", 52),
            ]
            for label, val in params:
                row, _ = _param_row(label, val, left)
                left_layout.addWidget(row)

            # Emotion
            emo_row = QHBoxLayout()
            emo_lbl = QLabel("Emotion", left)
            emo_lbl.setStyleSheet("font-size:12px;color:#A9B2C3;")
            emo_row.addWidget(emo_lbl)
            emo_combo = QComboBox(left)
            emo_combo.addItems(["Neutral", "Angry", "Sad", "Happy", "Fearful", "Surprised"])
            emo_combo.setCurrentIndex(1)
            emo_row.addWidget(emo_combo, 1)
            left_layout.addLayout(emo_row)

            int_lbl = QLabel("Intensity", left)
            int_lbl.setObjectName("SectionLabel")
            left_layout.addWidget(int_lbl)
            int_row, _ = _param_row("Intensity", 76, left)
            left_layout.addWidget(int_row)

            left_layout.addStretch()

            gen_btn = QPushButton("⚡  Generate Preview", left)
            gen_btn.setProperty("primary", "true")
            gen_btn.setFixedHeight(42)
            left_layout.addWidget(gen_btn)

            layout.addWidget(left)

            # ---- RIGHT: Takes + Comparison ----
            right = QVBoxLayout()
            right_frame = QFrame(content)
            right_frame.setObjectName("Panel")
            right_layout = QVBoxLayout(right_frame)
            right_layout.setContentsMargins(16, 16, 16, 16)
            right_layout.setSpacing(14)

            # Takes
            takes_lbl = QLabel("TAKES", right_frame)
            takes_lbl.setObjectName("SectionLabel")
            right_layout.addWidget(takes_lbl)

            takes_data = [(1, 92, False), (2, 96, True), (3, 94, False)]
            for num, score, active in takes_data:
                take = _TakeRow(num, score, active, right_frame)
                right_layout.addWidget(take)

            add_take_btn = QPushButton("＋  Generate New Take", right_frame)
            add_take_btn.setProperty("accent", "ai")
            right_layout.addWidget(add_take_btn)

            # Divider
            right_layout.addSpacing(8)
            div = QFrame(right_frame)
            div.setObjectName("DividerH")
            right_layout.addWidget(div)
            right_layout.addSpacing(8)

            # Comparison
            comp_lbl = QLabel("COMPARISON", right_frame)
            comp_lbl.setObjectName("SectionLabel")
            right_layout.addWidget(comp_lbl)

            for label, color in [("ORIGINAL", "#22D3EE"), ("DUBBED", "#4F8CFF")]:
                comp_row = QVBoxLayout()
                c_lbl = QLabel(label, right_frame)
                c_lbl.setStyleSheet(f"font-size:11px;font-weight:700;color:{color};")
                comp_row.addWidget(c_lbl)
                wf2 = WaveformWidget(color=color, parent=right_frame)
                wf2.setFixedHeight(48)
                comp_row.addWidget(wf2)
                play_row = QHBoxLayout()
                pb = QPushButton(f"▶  Play {label.title()}", right_frame)
                pb.setFixedHeight(30)
                play_row.addWidget(pb)
                play_row.addStretch()
                comp_row.addLayout(play_row)
                right_layout.addLayout(comp_row)

            # Scores
            scores_lbl = QLabel("QUALITY SCORES", right_frame)
            scores_lbl.setObjectName("SectionLabel")
            right_layout.addWidget(scores_lbl)

            score_data = [
                ("Voice Similarity", 96), ("Pitch Match", 92),
                ("Energy Match", 89), ("Emotion Match", 94),
            ]
            for sc_name, sc_val in score_data:
                sc_row = QHBoxLayout()
                sc_name_lbl = QLabel(sc_name, right_frame)
                sc_name_lbl.setStyleSheet("font-size:12px;color:#A9B2C3;")
                sc_row.addWidget(sc_name_lbl)
                sc_row.addStretch()
                sc_val_lbl = QLabel(f"{sc_val}%", right_frame)
                color = "#22C55E" if sc_val >= 90 else "#F59E0B"
                sc_val_lbl.setStyleSheet(f"font-size:13px;font-weight:700;color:{color};")
                sc_row.addWidget(sc_val_lbl)
                right_layout.addLayout(sc_row)

            right_layout.addStretch()
            layout.addWidget(right_frame, 1)

            scroll.setWidget(content)
            root.addWidget(scroll, 1)


__all__ = ["VoiceStudioScreen"]
