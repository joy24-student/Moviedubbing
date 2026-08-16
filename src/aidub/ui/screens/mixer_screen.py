"""
Audio Mixer screen — professional broadcast-grade DAW mixer.

Includes:
- Master fader
- Per-track channel strips (Dialogue / Music / FX / Ambience)
- VU meters
- Mute / Solo buttons
- Per-character gain table
- Acoustic environment selector
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSlider,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


_TRACKS = [
    ("Dialogue",  "#4F8CFF", -3.2,  0.72),
    ("Music",     "#10B981", -8.0,  0.45),
    ("Effects",   "#EC4899", -2.0,  0.68),
    ("Ambience",  "#22D3EE", -11.0, 0.28),
]

_CHARACTERS = [
    ("Tony",    1.2),
    ("Pepper", -0.5),
    ("Steve",   0.8),
    ("Narrator",-1.1),
    ("Nick",    0.4),
]

_ENVIRONMENTS = [
    "Studio Clean", "Small Room", "Large Room", "Hall",
    "Outdoor", "Car Interior", "Telephone", "Radio",
]


if _QT:

    class _ChannelStrip(QFrame):  # type: ignore[misc]
        """Single mixer channel strip."""

        volume_changed = Signal(str, float)
        muted = Signal(str, bool)
        soloed = Signal(str, bool)

        def __init__(
            self,
            name: str,
            color: str,
            db: float,
            level: float,
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self._name = name
            self._color = color
            self._muted = False
            self._soloed = False

            self.setFixedWidth(100)
            self.setObjectName("ChannelStrip")
            self.setStyleSheet(
                f"QFrame#ChannelStrip{{background:#161D28;"
                f"border:1px solid #283241;border-top:3px solid {color};"
                f"border-radius:8px;}}"
            )

            lay = QVBoxLayout(self)
            lay.setContentsMargins(8, 10, 8, 10)
            lay.setSpacing(6)

            # Track name
            name_lbl = QLabel(name, self)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet(f"font-size:11px;font-weight:700;color:{color};")
            lay.addWidget(name_lbl)

            # VU meter
            from aidub.ui.widgets.common import VuMeterWidget  # noqa: PLC0415
            self._vu = VuMeterWidget(self)
            self._vu.set_level(level)
            self._vu.setFixedHeight(100)
            lay.addWidget(self._vu, alignment=Qt.AlignmentFlag.AlignHCenter)

            # dB label
            self._db_lbl = QLabel(f"{db:+.1f} dB", self)
            self._db_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._db_lbl.setStyleSheet("font-size:12px;font-weight:700;color:#F7F9FC;font-family:'Cascadia Code';")
            lay.addWidget(self._db_lbl)

            # Fader
            self._fader = QSlider(Qt.Orientation.Vertical, self)
            self._fader.setRange(-600, 120)
            self._fader.setValue(int(db * 10))
            self._fader.setFixedHeight(120)
            self._fader.setStyleSheet(
                f"QSlider::groove:vertical{{width:6px;background:#283241;border-radius:3px;}}"
                f"QSlider::handle:vertical{{background:{color};width:16px;height:8px;margin:-5px;border-radius:4px;}}"
                f"QSlider::sub-page:vertical{{background:#283241;}}"
                f"QSlider::add-page:vertical{{background:{color};border-radius:3px;}}"
            )
            self._fader.valueChanged.connect(self._on_fader)
            lay.addWidget(self._fader, alignment=Qt.AlignmentFlag.AlignHCenter)

            # M / S buttons
            ms_row = QHBoxLayout()
            ms_row.setSpacing(4)
            self._mute_btn = QPushButton("M", self)
            self._mute_btn.setFixedSize(28, 24)
            self._mute_btn.setCheckable(True)
            self._mute_btn.setStyleSheet(
                "QPushButton{background:#1C2431;border:1px solid #283241;border-radius:4px;font-weight:700;font-size:11px;}"
                "QPushButton:checked{background:#EF4444;border-color:#EF4444;color:#fff;}"
            )
            self._mute_btn.toggled.connect(lambda c: self.muted.emit(self._name, c))
            ms_row.addWidget(self._mute_btn)

            self._solo_btn = QPushButton("S", self)
            self._solo_btn.setFixedSize(28, 24)
            self._solo_btn.setCheckable(True)
            self._solo_btn.setStyleSheet(
                "QPushButton{background:#1C2431;border:1px solid #283241;border-radius:4px;font-weight:700;font-size:11px;}"
                "QPushButton:checked{background:#F59E0B;border-color:#F59E0B;color:#000;}"
            )
            self._solo_btn.toggled.connect(lambda c: self.soloed.emit(self._name, c))
            ms_row.addWidget(self._solo_btn)
            lay.addLayout(ms_row)

        def _on_fader(self, value: int) -> None:
            db = value / 10.0
            self._db_lbl.setText(f"{db:+.1f} dB")
            self.volume_changed.emit(self._name, db)

        def animate_meter(self) -> None:
            import random  # noqa: PLC0415
            lvl = random.uniform(0.1, 0.85) if not self._muted else 0.0
            self._vu.set_level(lvl)

    class MixerScreen(QWidget):  # type: ignore[misc]
        """Audio Mixer — professional 9-track studio mixer."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._strips: list[_ChannelStrip] = []
            self._build_ui()
            self._start_meter_animation()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            # Title bar
            topbar = QFrame(self)
            topbar.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;")
            topbar.setFixedHeight(48)
            tb = QHBoxLayout(topbar)
            tb.setContentsMargins(16, 0, 16, 0)
            tb.addWidget(self._make_title("Audio Mixer"))
            tb.addStretch()
            for label, tip in [("Reset All", ""), ("Export Stems", ""), ("Auto-Mix AI", "ai")]:
                btn = QPushButton(label, topbar)
                btn.setFixedHeight(34)
                if tip == "ai":
                    btn.setProperty("accent", "ai")
                tb.addWidget(btn)
                tb.addSpacing(6)
            root.addWidget(topbar)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 24)
            layout.setSpacing(20)

            # ── Channel Strips ─────────────────────────────────────────
            strips_section = QVBoxLayout()
            strips_section.setSpacing(10)
            lbl = QLabel("CHANNEL STRIPS", content)
            lbl.setObjectName("SectionLabel")
            strips_section.addWidget(lbl)

            strips_row = QHBoxLayout()
            strips_row.setSpacing(10)

            # Master
            master = self._master_strip(content)
            strips_row.addWidget(master)

            # Separator
            div = QFrame(content)
            div.setObjectName("DividerV")
            div.setFixedWidth(1)
            strips_row.addWidget(div)

            # Per-track
            for name, color, db, level in _TRACKS:
                strip = _ChannelStrip(name, color, db, level, content)
                strips_row.addWidget(strip)
                self._strips.append(strip)

            strips_row.addStretch()
            strips_section.addLayout(strips_row)
            layout.addLayout(strips_section)

            # ── Per-Character Gain ─────────────────────────────────────
            char_group = QGroupBox("Per-Character Dialogue Gain", content)
            char_grid = QGridLayout(char_group)
            char_grid.setSpacing(10)
            for i, (char_name, gain) in enumerate(_CHARACTERS):
                n_lbl = QLabel(char_name, char_group)
                n_lbl.setObjectName("ValueLabel")
                slider = QSlider(Qt.Orientation.Horizontal, char_group)
                slider.setRange(-60, 60)
                slider.setValue(int(gain * 10))
                slider.setFixedWidth(200)
                gain_lbl = QLabel(f"{gain:+.1f} dB", char_group)
                gain_lbl.setStyleSheet("font-family:'Cascadia Code';font-size:12px;color:#A9B2C3;min-width:60px;")
                gain_lbl.setFixedWidth(60)
                slider.valueChanged.connect(
                    lambda v, gl=gain_lbl: gl.setText(f"{v/10:+.1f} dB")
                )
                char_grid.addWidget(n_lbl, i, 0)
                char_grid.addWidget(slider, i, 1)
                char_grid.addWidget(gain_lbl, i, 2)
            layout.addWidget(char_group)

            # ── Acoustic Environment ────────────────────────────────────
            env_group = QGroupBox("Acoustic Environment", content)
            env_grid = QGridLayout(env_group)
            env_grid.setSpacing(8)
            env_radio_group: list[QRadioButton] = []
            for i, env in enumerate(_ENVIRONMENTS):
                rb = QRadioButton(env, env_group)
                rb.setChecked(env == "Studio Clean")
                env_radio_group.append(rb)
                env_grid.addWidget(rb, i // 4, i % 4)

            auto_rb = QRadioButton("Match Original Automatically ★", env_group)
            auto_rb.setChecked(True)
            env_grid.addWidget(auto_rb, 2, 0, 1, 4)
            layout.addWidget(env_group)

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll, 1)

        def _master_strip(self, parent: QWidget) -> QFrame:
            frame = QFrame(parent)
            frame.setFixedWidth(80)
            frame.setObjectName("MasterStrip")
            frame.setStyleSheet(
                "QFrame#MasterStrip{background:#1C2431;border:1px solid #34415A;"
                "border-top:3px solid #F7F9FC;border-radius:8px;}"
            )
            lay = QVBoxLayout(frame)
            lay.setContentsMargins(8, 10, 8, 10)
            lay.setSpacing(6)

            QLabel_master = QLabel("MASTER", frame)
            QLabel_master.setAlignment(Qt.AlignmentFlag.AlignCenter)
            QLabel_master.setStyleSheet("font-size:10px;font-weight:700;color:#F7F9FC;")
            lay.addWidget(QLabel_master)

            from aidub.ui.widgets.common import VuMeterWidget  # noqa: PLC0415
            vu = VuMeterWidget(frame)
            vu.set_level(0.82)
            vu.setFixedHeight(100)
            lay.addWidget(vu, alignment=Qt.AlignmentFlag.AlignHCenter)

            db_lbl = QLabel("0.0 dB", frame)
            db_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            db_lbl.setStyleSheet("font-size:11px;font-weight:700;color:#F7F9FC;font-family:'Cascadia Code';")
            lay.addWidget(db_lbl)

            fader = QSlider(Qt.Orientation.Vertical, frame)
            fader.setRange(-600, 60)
            fader.setValue(0)
            fader.setFixedHeight(120)
            lay.addWidget(fader, alignment=Qt.AlignmentFlag.AlignHCenter)
            return frame

        @staticmethod
        def _make_title(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            return lbl

        def _start_meter_animation(self) -> None:
            timer = QTimer(self)
            timer.timeout.connect(self._tick_meters)
            timer.start(80)

        def _tick_meters(self) -> None:
            for strip in self._strips:
                strip.animate_meter()


__all__ = ["MixerScreen"]
