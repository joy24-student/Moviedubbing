"""
Quality Control Center screen.

Features:
- Overall dub score with 7-dimension breakdown
- Blocking / Warning / Info tabs
- Issue table with time / character / problem / score / fix action
- AI Fix All with confirmation dialog
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSplitter,
        QTabWidget,
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


_DIMENSIONS = [
    ("Translation", 97, "#A855F7"),
    ("Voice",       95, "#22D3EE"),
    ("Emotion",     91, "#EC4899"),
    ("Timing",      98, "#4F8CFF"),
    ("Lip Sync",    93, "#F59E0B"),
    ("Audio",       96, "#10B981"),
    ("Subtitle",    99, "#22C55E"),
]

_BLOCKING = [
    ("01:12:22", "Tony",   "Lip sync mismatch",        72),
    ("01:18:10", "Steve",  "Voice drift >15%",          77),
    ("01:31:02", "Pepper", "Dialogue too long (+32%)",  61),
    ("00:44:18", "Nick",   "Wrong speaker assignment",  55),
]

_WARNINGS = [
    ("00:09:44", "Tony",    "Timing delta +12%",          83),
    ("00:18:31", "Pepper",  "Emotion mismatch (sad→angry)",78),
    ("00:27:05", "Unknown", "Low ASR confidence (62%)",    71),
    ("00:55:22", "Steve",   "Subtitle speed 21 CPS",       80),
    ("01:02:14", "Tony",    "Pitch drift on long phrase",   82),
    ("01:45:38", "Natasha", "Translation style deviation", 76),
]

_INFO = [
    ("00:03:12", "All",    "Scene boundary uncertainty",   91),
    ("00:11:55", "Tony",   "Breath artifact (minor)",      93),
    ("00:29:41", "Music",  "Loudness -2dB below target",   88),
]


if _QT:

    class _ScoreDonut(QWidget):  # type: ignore[misc]
        """Large overall score display."""

        def __init__(self, score: float, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._score = score
            self.setFixedSize(140, 140)

        def paintEvent(self, _ev: object) -> None:  # noqa: N802
            from PySide6.QtGui import QColor, QPainter, QPen, QFont  # noqa: PLC0415
            from PySide6.QtCore import QRectF  # noqa: PLC0415
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            cx, cy, r = self.width() / 2, self.height() / 2, 54

            # Background ring
            p.setPen(QPen(QColor("#283241"), 12))
            p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

            # Score arc
            color = "#22C55E" if self._score >= 90 else "#F59E0B" if self._score >= 70 else "#EF4444"
            p.setPen(QPen(QColor(color), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            span = int(self._score / 100 * 360 * 16)
            p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 90 * 16, -span)

            # Score text
            font = QFont("Segoe UI Variable", 22)
            font.setBold(True)
            p.setFont(font)
            p.setPen(QColor("#F7F9FC"))
            p.drawText(QRectF(cx - 40, cy - 20, 80, 38), Qt.AlignmentFlag.AlignCenter,
                       f"{self._score:.1f}")

            font2 = QFont("Segoe UI Variable", 9)
            p.setFont(font2)
            p.setPen(QColor("#687386"))
            p.drawText(QRectF(cx - 40, cy + 18, 80, 22), Qt.AlignmentFlag.AlignCenter, "/ 100")
            p.end()

    def _issue_table(issues: list, parent: QWidget, with_fix: bool = True) -> QTableWidget:
        headers = ["Time", "Character", "Problem", "Score"]
        if with_fix:
            headers.append("Action")
        tbl = QTableWidget(len(issues), len(headers), parent)
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setStyleSheet(
            "QTableWidget{background:#0D1118;border:none;gridline-color:#1C2431;}"
            "QTableWidget::item{padding:8px;border-bottom:1px solid #161D28;}"
            "QTableWidget::item:selected{background:#1E3A5F;}"
            "QHeaderView::section{background:#161D28;border:none;border-bottom:1px solid #283241;"
            "padding:8px;font-weight:700;color:#A9B2C3;font-size:12px;}"
        )

        for r, (ts, char, prob, score) in enumerate(issues):
            for c, val in enumerate([ts, char, prob]):
                item = QTableWidgetItem(val)
                item.setForeground(
                    Qt.GlobalColor.white if c != 0
                    else Qt.GlobalColor.gray
                )
                tbl.setItem(r, c, item)

            score_item = QTableWidgetItem(f"{score}%")
            color = "#EF4444" if score < 70 else "#F59E0B" if score < 85 else "#22C55E"
            from PySide6.QtGui import QColor  # noqa: PLC0415
            score_item.setForeground(QColor(color))
            tbl.setItem(r, 3, score_item)

            if with_fix:
                fix_lbl = QTableWidgetItem("Fix →")
                fix_lbl.setForeground(QColor("#4F8CFF"))
                tbl.setItem(r, 4, fix_lbl)

        tbl.resizeColumnsToContents()
        return tbl

    class QualityControlScreen(QWidget):  # type: ignore[misc]
        """Quality Control Center — full QC dashboard."""

        fix_requested = Signal(str)

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
            lbl = QLabel("Quality Control", self)
            lbl.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(lbl)
            tb.addStretch()
            run_btn = QPushButton("▶  Run QC Analysis", self)
            run_btn.setProperty("primary", "true")
            tb.addWidget(run_btn)
            tb.addSpacing(8)
            fix_all_btn = QPushButton("🤖  AI Fix All", self)
            fix_all_btn.setProperty("accent", "ai")
            fix_all_btn.clicked.connect(self._on_ai_fix_all)
            tb.addWidget(fix_all_btn)
            root.addWidget(topbar)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 24)
            layout.setSpacing(20)

            # ── Score dashboard ────────────────────────────────────────
            dash_row = QHBoxLayout()
            dash_row.setSpacing(20)

            # Overall donut
            overall_frame = QFrame(content)
            overall_frame.setObjectName("Panel")
            ov_lay = QVBoxLayout(overall_frame)
            ov_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ov_lay.setContentsMargins(16, 16, 16, 16)
            ov_lbl = QLabel("OVERALL", overall_frame)
            ov_lbl.setObjectName("SectionLabel")
            ov_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ov_lay.addWidget(ov_lbl)
            donut = _ScoreDonut(94.8, overall_frame)
            ov_lay.addWidget(donut)
            overall_frame.setFixedWidth(180)
            dash_row.addWidget(overall_frame)

            # Dimension grid
            dim_frame = QFrame(content)
            dim_frame.setObjectName("Panel")
            dim_lay = QGridLayout(dim_frame)
            dim_lay.setSpacing(10)
            dim_lay.setContentsMargins(16, 16, 16, 16)
            for i, (dim, score, color) in enumerate(_DIMENSIONS):
                name_lbl = QLabel(dim, dim_frame)
                name_lbl.setObjectName("MetaLabel")
                dim_lay.addWidget(name_lbl, i, 0)

                from PySide6.QtWidgets import QProgressBar  # noqa: PLC0415
                bar = QProgressBar(dim_frame)
                bar.setRange(0, 100)
                bar.setValue(score)
                bar.setTextVisible(False)
                bar.setFixedHeight(7)
                bar.setStyleSheet(
                    f"QProgressBar{{background:#283241;border-radius:3px;border:none;}}"
                    f"QProgressBar::chunk{{background:{color};border-radius:3px;}}"
                )
                dim_lay.addWidget(bar, i, 1)

                val_lbl = QLabel(f"{score}%", dim_frame)
                val_lbl.setFixedWidth(36)
                val_lbl.setStyleSheet(f"font-size:13px;font-weight:700;color:{color};")
                dim_lay.addWidget(val_lbl, i, 2)
            dash_row.addWidget(dim_frame, 1)

            # Issue count cards
            issue_col = QVBoxLayout()
            issue_col.setSpacing(8)
            for label, count, color in [
                ("BLOCKING", len(_BLOCKING), "#EF4444"),
                ("WARNING",  len(_WARNINGS), "#F59E0B"),
                ("INFO",     len(_INFO),     "#4F8CFF"),
            ]:
                card = QFrame(content)
                card.setObjectName("Card")
                card.setFixedSize(90, 75)
                c_lay = QVBoxLayout(card)
                c_lay.setContentsMargins(10, 10, 10, 10)
                c_lay.setSpacing(4)
                cnt_lbl = QLabel(str(count), card)
                cnt_lbl.setStyleSheet(f"font-size:26px;font-weight:700;color:{color};")
                cnt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                c_lay.addWidget(cnt_lbl)
                typ_lbl = QLabel(label, card)
                typ_lbl.setStyleSheet(f"font-size:10px;font-weight:700;color:{color};")
                typ_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                c_lay.addWidget(typ_lbl)
                issue_col.addWidget(card)
            dash_row.addLayout(issue_col)
            layout.addLayout(dash_row)

            # ── Issue tabs ─────────────────────────────────────────────
            tabs = QTabWidget(content)
            tabs.addTab(_issue_table(_BLOCKING, tabs), f"⛔  Blocking ({len(_BLOCKING)})")
            tabs.addTab(_issue_table(_WARNINGS, tabs), f"⚠  Warnings ({len(_WARNINGS)})")
            tabs.addTab(_issue_table(_INFO, tabs, with_fix=False), f"ℹ  Info ({len(_INFO)})")
            layout.addWidget(tabs, 1)

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll, 1)

        def _on_ai_fix_all(self) -> None:
            from PySide6.QtWidgets import QMessageBox  # noqa: PLC0415
            msg = QMessageBox(self)
            msg.setWindowTitle("AI Fix All — Confirm")
            msg.setText(
                "<b>AI will attempt to fix:</b><br>"
                f"• {len(_BLOCKING)} blocking issues<br>"
                f"• {len(_WARNINGS)} warnings<br><br>"
                "<i>Approved and Locked dialogue will NOT be modified.</i>"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            msg.button(QMessageBox.StandardButton.Ok).setText("Apply")
            msg.exec()


__all__ = ["QualityControlScreen"]
