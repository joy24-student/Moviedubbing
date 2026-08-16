"""
Render Queue screen.

Shows active render job with live stage progress,
pending jobs list, and stage checklist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import QTimer, Qt, Signal
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W

_STAGES = [
    ("Translation",  True,  100),
    ("Voice",        True,  100),
    ("Timing",       True,  100),
    ("Lip Sync",     False,  82),
    ("Audio Mix",    False,   0),
    ("QC",           False,   0),
    ("Export",       False,   0),
]

_PENDING = [
    ("Avengers Hindi",   "Waiting", "#687386"),
    ("Avengers Spanish", "Waiting", "#687386"),
    ("Trailer Bengali",  "Waiting", "#687386"),
    ("Short Clip Test",  "Paused",  "#F59E0B"),
]


if _QT:

    class _PendingRow(QFrame):  # type: ignore[misc]
        def __init__(self, name: str, status: str, color: str, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("ElevatedPanel")
            self.setStyleSheet("QFrame#ElevatedPanel{background:#1C2431;border:1px solid #283241;border-radius:7px;}")
            lay = QHBoxLayout(self)
            lay.setContentsMargins(14, 10, 14, 10)
            n = QLabel(name, self)
            n.setStyleSheet("font-size:13px;font-weight:600;color:#F7F9FC;")
            lay.addWidget(n)
            lay.addStretch()
            s = QLabel(status, self)
            s.setStyleSheet(f"font-size:12px;font-weight:600;color:{color};")
            lay.addWidget(s)

    class RenderQueueScreen(QWidget):  # type: ignore[misc]
        """Render Queue — active job + pending list."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._sim_pct = 82
            self._sim_scene = 152
            self._build_ui()
            self._start_simulation()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            topbar = QFrame(self)
            topbar.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;")
            topbar.setFixedHeight(48)
            tb = QHBoxLayout(topbar)
            tb.setContentsMargins(16, 0, 16, 0)
            tb.addWidget(self._lbl("Render Queue", size=18, weight=700))
            tb.addStretch()
            tb.addWidget(self._btn("＋ New Render", primary=True))
            root.addWidget(topbar)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 24)
            layout.setSpacing(20)

            # ── Active Job ─────────────────────────────────────────────
            layout.addWidget(self._section("ACTIVE JOB"))

            active_frame = QFrame(content)
            active_frame.setObjectName("Panel")
            af_lay = QVBoxLayout(active_frame)
            af_lay.setContentsMargins(20, 16, 20, 16)
            af_lay.setSpacing(12)

            # Title + pct
            top_row = QHBoxLayout()
            self._job_title = QLabel("Avengers Bengali Dub", active_frame)
            self._job_title.setStyleSheet("font-size:16px;font-weight:700;color:#F7F9FC;")
            top_row.addWidget(self._job_title)
            top_row.addStretch()
            self._pct_lbl = QLabel("82%", active_frame)
            self._pct_lbl.setStyleSheet("font-size:22px;font-weight:700;color:#4F8CFF;")
            top_row.addWidget(self._pct_lbl)
            af_lay.addLayout(top_row)

            self._main_bar = QProgressBar(active_frame)
            self._main_bar.setRange(0, 100)
            self._main_bar.setValue(82)
            self._main_bar.setTextVisible(False)
            self._main_bar.setFixedHeight(10)
            af_lay.addWidget(self._main_bar)

            # Stage / scene info
            info_grid = QGridLayout()
            info_grid.setSpacing(8)
            meta = [
                ("Current Stage", "Lip Sync", 0, 0),
                ("Scene",         "152 / 179", 0, 2),
                ("GPU Usage",     "91%",       1, 0),
                ("VRAM",          "10.2 / 12 GB", 1, 2),
                ("Est. Remaining","18m 22s",   2, 0),
                ("Elapsed",       "1h 14m",    2, 2),
            ]
            for key, val, r, c in meta:
                k = QLabel(key, active_frame)
                k.setObjectName("MetaLabel")
                v = QLabel(val, active_frame)
                v.setObjectName("ValueLabel")
                info_grid.addWidget(k, r, c)
                info_grid.addWidget(v, r, c + 1)
            af_lay.addLayout(info_grid)

            # Controls
            ctrl = QHBoxLayout()
            ctrl.setSpacing(8)
            for label, accent in [("⏸ Pause", ""), ("■ Stop", "danger"), ("→ Background", "")]:
                btn = QPushButton(label, active_frame)
                btn.setFixedHeight(34)
                if accent:
                    btn.setProperty("accent", accent)
                ctrl.addWidget(btn)
            ctrl.addStretch()
            af_lay.addLayout(ctrl)

            layout.addWidget(active_frame)

            # ── Stage Checklist ────────────────────────────────────────
            layout.addWidget(self._section("PIPELINE STAGES"))

            stages_frame = QFrame(content)
            stages_frame.setObjectName("Panel")
            sf_lay = QVBoxLayout(stages_frame)
            sf_lay.setContentsMargins(16, 14, 16, 14)
            sf_lay.setSpacing(8)

            for stage_name, done, pct in _STAGES:
                row = QHBoxLayout()
                if done and pct == 100:
                    icon = QLabel("✓", stages_frame)
                    icon.setStyleSheet("font-size:14px;color:#22C55E;font-weight:700;min-width:20px;")
                elif pct > 0:
                    icon = QLabel("●", stages_frame)
                    icon.setStyleSheet("font-size:14px;color:#4F8CFF;min-width:20px;")
                else:
                    icon = QLabel("○", stages_frame)
                    icon.setStyleSheet("font-size:14px;color:#687386;min-width:20px;")
                row.addWidget(icon)

                name_lbl = QLabel(stage_name, stages_frame)
                name_lbl.setStyleSheet(
                    "font-size:13px;color:#F7F9FC;" if pct > 0
                    else "font-size:13px;color:#687386;"
                )
                row.addWidget(name_lbl)
                row.addStretch()

                if 0 < pct < 100:
                    bar = QProgressBar(stages_frame)
                    bar.setRange(0, 100)
                    bar.setValue(pct)
                    bar.setTextVisible(False)
                    bar.setFixedSize(80, 6)
                    row.addWidget(bar)
                    val = QLabel(f"{pct}%", stages_frame)
                    val.setStyleSheet("font-size:12px;color:#4F8CFF;font-weight:700;min-width:32px;")
                    row.addWidget(val)
                elif pct == 100:
                    val = QLabel("Done", stages_frame)
                    val.setStyleSheet("font-size:12px;color:#22C55E;")
                    row.addWidget(val)
                else:
                    val = QLabel("Waiting", stages_frame)
                    val.setStyleSheet("font-size:12px;color:#687386;")
                    row.addWidget(val)

                sf_lay.addLayout(row)
            layout.addWidget(stages_frame)

            # ── Pending Jobs ───────────────────────────────────────────
            layout.addWidget(self._section("QUEUE"))
            for name, status, color in _PENDING:
                layout.addWidget(_PendingRow(name, status, color, content))

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll, 1)

        @staticmethod
        def _lbl(text: str, size: int = 13, weight: int = 400, color: str = "#F7F9FC") -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-size:{size}px;font-weight:{weight};color:{color};")
            return lbl

        @staticmethod
        def _btn(text: str, primary: bool = False) -> QPushButton:
            btn = QPushButton(text)
            btn.setFixedHeight(34)
            if primary:
                btn.setProperty("primary", "true")
            return btn

        @staticmethod
        def _section(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("SectionLabel")
            return lbl

        def _start_simulation(self) -> None:
            timer = QTimer(self)
            timer.timeout.connect(self._tick)
            timer.start(2000)

        def _tick(self) -> None:
            if self._sim_pct < 100:
                self._sim_pct = min(100, self._sim_pct + 1)
                self._main_bar.setValue(self._sim_pct)
                self._pct_lbl.setText(f"{self._sim_pct}%")
            if self._sim_scene < 179:
                self._sim_scene += 1


__all__ = ["RenderQueueScreen"]
