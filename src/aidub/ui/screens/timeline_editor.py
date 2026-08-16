"""
Full QGraphicsView-based interactive Timeline Editor.

Tracks:
  V1 VIDEO       — video source blocks
  V2 LIP SYNC    — lip-sync overlay segments
  A1 ORIGINAL    — original dialogue waveform
  A2 DIALOGUE    — dubbed dialogue clips
  A3 MUSIC       — music track
  A4 FX          — sound effects
  A5 AMBIENCE    — ambience track
  S1 ENGLISH     — English subtitle markers
  S2 BENGALI     — Bengali subtitle markers

Interactions:
  Click           select clip
  Ctrl+Click      multi-select
  Drag            move clip
  Ctrl+Wheel      zoom
  Wheel           scroll
  Double-click    open clip properties
  Right-click     context menu (AI actions)
  J/K/L           shuttle playback
  Space           play/pause
  S               blade split
  Delete          remove
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import (
        QLineF,
        QPointF,
        QRectF,
        Qt,
        QTimer,
        Signal,
    )
    from PySide6.QtGui import (
        QAction,
        QBrush,
        QColor,
        QFont,
        QPainter,
        QPen,
        QWheelEvent,
    )
    from PySide6.QtWidgets import (
        QFrame,
        QGraphicsItem,
        QGraphicsRectItem,
        QGraphicsScene,
        QGraphicsView,
        QHBoxLayout,
        QLabel,
        QMenu,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W

# ────────────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────────────
TRACK_HEIGHT = 44
TRACK_HEADER_WIDTH = 130
RULER_HEIGHT = 32
MIN_CLIP_WIDTH = 4
PX_PER_SEC_DEFAULT = 80.0

_TRACK_DEFS = [
    # (id, label, color, type)
    ("V1", "VIDEO",      "#3B82F6", "video"),
    ("V2", "LIP SYNC",   "#8B5CF6", "video"),
    ("A1", "ORIGINAL",   "#10B981", "audio"),
    ("A2", "DIALOGUE",   "#6366F1", "audio"),
    ("A3", "MUSIC",      "#F59E0B", "audio"),
    ("A4", "FX",         "#EC4899", "audio"),
    ("A5", "AMBIENCE",   "#14B8A6", "audio"),
    ("S1", "ENGLISH",    "#F97316", "subtitle"),
    ("S2", "BENGALI",    "#06B6D4", "subtitle"),
]

# Demo clips: (track_id, start_sec, dur_sec, label, score)
_DEMO_CLIPS = [
    ("V1",  0,  8000, "Movie",      None),
    ("V2",  142, 4.2, "LS #001",    94),
    ("V2",  290, 3.8, "LS #002",    88),
    ("A1",  0,  8000, "Original",   None),
    ("A2",  14,  2.8, "Tony",       96),
    ("A2",  18,  2.1, "Pepper",     94),
    ("A2",  22,  2.6, "Tony",       91),
    ("A2",  27,  1.9, "Steve",      98),
    ("A2",  31,  0.8, "Tony",       99),
    ("A2",  36,  2.4, "Pepper",     89),
    ("A3",  0,  8000, "Score",      None),
    ("A4",  14,  1.2, "Impact",     None),
    ("A4",  290, 0.8, "Whoosh",     None),
    ("A5",  0,  8000, "Ambience",   None),
    ("S1",  14,  2.8, "I told you…",None),
    ("S1",  18,  2.1, "You never…", None),
    ("S2",  14,  2.8, "আমি তোমাকে…",None),
    ("S2",  18,  2.1, "তুমি কখনো…", None),
]


if _QT:

    # ─────────────────────────────────────────────────────────────────────
    # Ruler item
    # ─────────────────────────────────────────────────────────────────────
    class _RulerItem(QGraphicsItem):  # type: ignore[misc]
        def __init__(self, duration_sec: float, px_per_sec: float) -> None:
            super().__init__()
            self._dur = duration_sec
            self._pps = px_per_sec
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        def boundingRect(self) -> QRectF:
            return QRectF(0, 0, self._dur * self._pps, RULER_HEIGHT)

        def paint(self, painter: QPainter, _opt: object, _widget: object = None) -> None:
            w = self._dur * self._pps
            painter.fillRect(QRectF(0, 0, w, RULER_HEIGHT), QColor("#0D1118"))
            painter.setPen(QPen(QColor("#283241"), 1))
            painter.drawLine(QLineF(0, RULER_HEIGHT - 1, w, RULER_HEIGHT - 1))

            font = QFont("Cascadia Code", 9)
            painter.setFont(font)
            painter.setPen(QColor("#687386"))

            # Choose tick spacing based on zoom
            pps = self._pps
            if pps >= 200:
                major, minor = 1, 0.25
            elif pps >= 80:
                major, minor = 5, 1
            elif pps >= 30:
                major, minor = 10, 5
            elif pps >= 10:
                major, minor = 30, 10
            else:
                major, minor = 60, 15

            t = 0.0
            while t <= self._dur:
                x = t * pps
                is_major = (t % major < 0.01)
                tick_h = 14 if is_major else 7
                col = QColor("#687386") if is_major else QColor("#283241")
                painter.setPen(QPen(col, 1))
                painter.drawLine(QLineF(x, RULER_HEIGHT - tick_h, x, RULER_HEIGHT))
                if is_major:
                    mins = int(t // 60)
                    secs = int(t % 60)
                    frames = int((t % 1) * 24)
                    label = f"{mins:02d}:{secs:02d}"
                    if pps >= 80:
                        label += f".{frames:02d}"
                    painter.setPen(QColor("#A9B2C3"))
                    painter.drawText(int(x) + 3, RULER_HEIGHT - 16, label)
                t += minor

    # ─────────────────────────────────────────────────────────────────────
    # Clip item
    # ─────────────────────────────────────────────────────────────────────
    class _ClipItem(QGraphicsRectItem):  # type: ignore[misc]
        def __init__(
            self,
            track_color: str,
            label: str,
            start_sec: float,
            dur_sec: float,
            score: int | None,
            px_per_sec: float,
            y: float,
            track_type: str,
        ) -> None:
            x = start_sec * px_per_sec
            w = max(MIN_CLIP_WIDTH, dur_sec * px_per_sec)
            h = TRACK_HEIGHT - 6
            super().__init__(QRectF(x, y, w, h))
            self._label = label
            self._score = score
            self._color = track_color
            self._track_type = track_type
            self._selected_override = False

            fill = QColor(track_color)
            fill.setAlpha(55)
            self.setBrush(QBrush(fill))
            border = QColor(track_color)
            border.setAlpha(180)
            self.setPen(QPen(border, 1.0))
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.setAcceptHoverEvents(True)

        def hoverEnterEvent(self, _ev: object) -> None:  # noqa: N802
            border = QColor(self._color)
            border.setAlpha(255)
            self.setPen(QPen(border, 2.0))

        def hoverLeaveEvent(self, _ev: object) -> None:  # noqa: N802
            if not self.isSelected():
                border = QColor(self._color)
                border.setAlpha(180)
                self.setPen(QPen(border, 1.0))

        def paint(self, painter: QPainter, opt: object, widget: object = None) -> None:
            super().paint(painter, opt, widget)
            r = self.rect()
            if r.width() < 20:
                return

            painter.setClipRect(r)
            # Label
            if self._track_type in ("audio", "subtitle") and r.width() > 30:
                font = QFont("Segoe UI Variable", 9)
                font.setWeight(QFont.Weight.Bold if self._track_type == "audio" else QFont.Weight.Normal)
                painter.setFont(font)
                painter.setPen(QColor("#F7F9FC"))
                text_rect = r.adjusted(4, 2, -4, -2)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 self._label)

            # Score badge
            if self._score is not None and r.width() > 50:
                color = "#22C55E" if self._score >= 90 else "#F59E0B" if self._score >= 75 else "#EF4444"
                badge = f"{self._score}%"
                font_b = QFont("Segoe UI Variable", 8)
                font_b.setBold(True)
                painter.setFont(font_b)
                painter.setPen(QColor(color))
                painter.drawText(
                    r.adjusted(4, -2, -4, 0),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                    badge,
                )

        def contextMenuEvent(self, event: object) -> None:  # noqa: N802
            if not hasattr(event, "screenPos"):
                return
            menu = QMenu()
            menu.setStyleSheet(
                "QMenu{background:#1C2431;border:1px solid #34415A;border-radius:8px;padding:4px;}"
                "QMenu::item{padding:8px 24px;border-radius:5px;}"
                "QMenu::item:selected{background:#1E3A5F;}"
            )
            menu.addSection("AI ACTIONS")
            for label in ["Regenerate Voice", "Match Original Voice", "Improve Emotion",
                          "Match Timing", "Fix Lip Sync", "Rewrite Translation"]:
                menu.addAction(label)
            menu.addSeparator()
            menu.addSection("EDITORIAL")
            for label in ["Approve ✓", "Lock 🔒", "Duplicate Take", "Compare Takes"]:
                menu.addAction(label)
            menu.addSeparator()
            menu.addAction("Properties…")
            menu.exec(event.screenPos())  # type: ignore[attr-defined]

    # ─────────────────────────────────────────────────────────────────────
    # Track header items (painted on left panel)
    # ─────────────────────────────────────────────────────────────────────
    class _TrackHeaderPanel(QWidget):  # type: ignore[misc]
        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setFixedWidth(TRACK_HEADER_WIDTH)
            self.setStyleSheet("background:#161D28;border-right:1px solid #283241;")

        def set_scroll_offset(self, y: int) -> None:
            self._scroll_y = y
            self.update()

        def paintEvent(self, _ev: object) -> None:  # noqa: N802
            painter = QPainter(self)
            painter.fillRect(0, 0, self.width(), self.height(), QColor("#161D28"))

            # Ruler header cell
            painter.fillRect(0, 0, self.width(), RULER_HEIGHT, QColor("#0D1118"))
            painter.setPen(QPen(QColor("#283241"), 1))
            painter.drawLine(0, RULER_HEIGHT - 1, self.width(), RULER_HEIGHT - 1)

            font = QFont("Segoe UI Variable", 9)
            font.setBold(True)
            painter.setFont(font)

            scroll_y = getattr(self, "_scroll_y", 0)
            y_base = RULER_HEIGHT - scroll_y
            for track_id, label, color, _ in _TRACK_DEFS:
                y = y_base
                y_base += TRACK_HEIGHT

                # Track cell background
                bg = QColor("#161D28") if track_id.startswith("V") else \
                     QColor("#131820") if track_id.startswith("A") else QColor("#141921")
                painter.fillRect(0, y, self.width(), TRACK_HEIGHT, bg)

                # Color swatch
                swatch = QColor(color)
                swatch.setAlpha(180)
                painter.fillRect(0, y, 4, TRACK_HEIGHT, swatch)

                # Label
                painter.setPen(QColor("#A9B2C3"))
                painter.drawText(8, y, self.width() - 8, TRACK_HEIGHT,
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 f"{track_id}  {label}")

                # Track separator
                painter.setPen(QPen(QColor("#283241"), 1))
                painter.drawLine(0, y + TRACK_HEIGHT - 1, self.width(), y + TRACK_HEIGHT - 1)

            painter.end()

    # ─────────────────────────────────────────────────────────────────────
    # Timeline Graphics View
    # ─────────────────────────────────────────────────────────────────────
    class _TimelineView(QGraphicsView):  # type: ignore[misc]
        timecode_changed = Signal(float)  # current position in seconds
        clip_selected = Signal(object)

        def __init__(
            self,
            scene: QGraphicsScene,
            header_panel: _TrackHeaderPanel,
            parent: _W | None = None,
        ) -> None:
            super().__init__(scene, parent)
            self._header = header_panel
            self._px_per_sec = PX_PER_SEC_DEFAULT
            self._duration = 7940.0  # ~02:11:40
            self._playhead_sec = 0.0
            self._playhead_item: QGraphicsRectItem | None = None
            self._playing = False

            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.setStyleSheet("QGraphicsView{background:#0D1118;border:none;}")
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setOptimizationFlag(
                QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True
            )
            self.setViewportUpdateMode(
                QGraphicsView.ViewportUpdateMode.SmartViewportUpdate
            )
            self.verticalScrollBar().valueChanged.connect(self._on_vscroll)

            self._playback_timer = QTimer(self)
            self._playback_timer.setInterval(33)
            self._playback_timer.timeout.connect(self._advance_playhead)

        def _on_vscroll(self, value: int) -> None:
            self._header.set_scroll_offset(value)

        def build_scene(self) -> None:
            sc = self.scene()
            sc.clear()
            self._playhead_item = None

            total_w = self._duration * self._px_per_sec + 200
            total_h = RULER_HEIGHT + len(_TRACK_DEFS) * TRACK_HEIGHT + 40
            sc.setSceneRect(0, 0, total_w, total_h)

            # Ruler
            ruler = _RulerItem(self._duration, self._px_per_sec)
            sc.addItem(ruler)

            # Track backgrounds (alternating)
            for i, (track_id, _, color, _) in enumerate(_TRACK_DEFS):
                y = RULER_HEIGHT + i * TRACK_HEIGHT
                bg_col = QColor("#0D1118") if i % 2 == 0 else QColor("#080B10")
                bg = sc.addRect(QRectF(0, y, total_w, TRACK_HEIGHT), QPen(Qt.PenStyle.NoPen), QBrush(bg_col))

                # Track separator line
                sep = sc.addLine(QLineF(0, y + TRACK_HEIGHT - 1, total_w, y + TRACK_HEIGHT - 1),
                                 QPen(QColor("#1A2234"), 1))

            # Clips
            track_y: dict[str, float] = {
                t[0]: RULER_HEIGHT + i * TRACK_HEIGHT + 3
                for i, t in enumerate(_TRACK_DEFS)
            }
            track_color_map = {t[0]: t[2] for t in _TRACK_DEFS}
            track_type_map = {t[0]: t[3] for t in _TRACK_DEFS}

            for (tid, start, dur, label, score) in _DEMO_CLIPS:
                clip = _ClipItem(
                    track_color_map.get(tid, "#4F8CFF"),
                    label,
                    float(start),
                    float(dur),
                    score,
                    self._px_per_sec,
                    track_y.get(tid, 0),
                    track_type_map.get(tid, "audio"),
                )
                sc.addItem(clip)

            # Playhead
            ph_x = self._playhead_sec * self._px_per_sec
            self._playhead_item = sc.addRect(
                QRectF(ph_x, 0, 1.5, total_h),
                QPen(Qt.PenStyle.NoPen),
                QBrush(QColor("#F7F9FC")),
            )
            self._playhead_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            self._playhead_item.setZValue(100)

        def set_playhead(self, sec: float) -> None:
            self._playhead_sec = max(0.0, min(sec, self._duration))
            if self._playhead_item:
                r = self._playhead_item.rect()
                self._playhead_item.setRect(
                    QRectF(self._playhead_sec * self._px_per_sec, 0, r.width(), r.height())
                )
            self.timecode_changed.emit(self._playhead_sec)

        def toggle_play(self) -> None:
            self._playing = not self._playing
            if self._playing:
                self._playback_timer.start()
            else:
                self._playback_timer.stop()

        def _advance_playhead(self) -> None:
            self.set_playhead(self._playhead_sec + 0.033)
            if self._playhead_sec >= self._duration:
                self.toggle_play()

        def zoom_in(self) -> None:
            self._px_per_sec = min(self._px_per_sec * 1.3, 800.0)
            self.build_scene()

        def zoom_out(self) -> None:
            self._px_per_sec = max(self._px_per_sec / 1.3, 2.0)
            self.build_scene()

        def wheelEvent(self, event: QWheelEvent) -> None:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.zoom_in()
                else:
                    self.zoom_out()
                event.accept()
            else:
                super().wheelEvent(event)

        def mousePressEvent(self, event: object) -> None:  # noqa: N802
            if hasattr(event, "button"):
                super().mousePressEvent(event)  # type: ignore[arg-type]
                # Click on empty area → move playhead
                scene_pos = self.mapToScene(event.pos())  # type: ignore[attr-defined]
                if scene_pos.y() < RULER_HEIGHT and self.scene():
                    self.set_playhead(scene_pos.x() / self._px_per_sec)

        def keyPressEvent(self, event: object) -> None:  # noqa: N802
            if not hasattr(event, "key"):
                super().keyPressEvent(event)  # type: ignore[arg-type]
                return
            k = event.key()  # type: ignore[attr-defined]
            from PySide6.QtCore import Qt as _Qt  # noqa: PLC0415
            if k == _Qt.Key.Key_Space:
                self.toggle_play()
            elif k == _Qt.Key.Key_J:
                self.set_playhead(self._playhead_sec - 5.0)
            elif k == _Qt.Key.Key_K:
                if self._playing:
                    self.toggle_play()
            elif k == _Qt.Key.Key_L:
                self.set_playhead(self._playhead_sec + 5.0)
            elif k == _Qt.Key.Key_Left:
                self.set_playhead(self._playhead_sec - 1.0 / 24.0)
            elif k == _Qt.Key.Key_Right:
                self.set_playhead(self._playhead_sec + 1.0 / 24.0)
            elif k == _Qt.Key.Key_Plus or k == _Qt.Key.Key_Equal:
                self.zoom_in()
            elif k == _Qt.Key.Key_Minus:
                self.zoom_out()
            else:
                super().keyPressEvent(event)  # type: ignore[arg-type]

    # ─────────────────────────────────────────────────────────────────────
    # Timeline Screen (full widget)
    # ─────────────────────────────────────────────────────────────────────
    class TimelineScreen(QWidget):  # type: ignore[misc]
        """Main Timeline Editor — full QGraphicsView NLE timeline."""

        clip_selected = Signal(object)

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            # ── Video Viewer stub ──────────────────────────────────────
            viewer_bar = QFrame(self)
            viewer_bar.setStyleSheet("background:#080B10;border-bottom:1px solid #283241;")
            viewer_bar.setFixedHeight(220)
            vb_layout = QHBoxLayout(viewer_bar)
            vb_layout.setContentsMargins(0, 0, 0, 0)
            vb_layout.setSpacing(0)

            # Original video panel
            for label, flex in [("ORIGINAL", 1), ("DUBBED", 1)]:
                pane = QFrame(viewer_bar)
                pane.setStyleSheet(
                    "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                    "stop:0 #0D1118,stop:1 #080B10);"
                    "border:none;"
                )
                pane_lay = QVBoxLayout(pane)
                pane_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
                p_icon = QLabel("🎬", pane)
                p_icon.setStyleSheet("font-size:40px;background:transparent;border:none;")
                p_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pane_lay.addWidget(p_icon)
                p_lbl = QLabel(label, pane)
                p_lbl.setStyleSheet("font-size:11px;font-weight:700;color:#687386;background:transparent;border:none;")
                p_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pane_lay.addWidget(p_lbl)
                vb_layout.addWidget(pane, flex)
                if label == "ORIGINAL":
                    div = QFrame(viewer_bar)
                    div.setObjectName("DividerV")
                    div.setFixedWidth(1)
                    vb_layout.addWidget(div)

            root.addWidget(viewer_bar)

            # ── Transport controls ─────────────────────────────────────
            transport = QFrame(self)
            transport.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;")
            transport.setFixedHeight(44)
            t_lay = QHBoxLayout(transport)
            t_lay.setContentsMargins(10, 0, 10, 0)
            t_lay.setSpacing(4)

            self._tc_label = QLabel("00:00:00.000", transport)
            self._tc_label.setStyleSheet(
                "font-family:'Cascadia Code';font-size:15px;font-weight:700;"
                "color:#F7F9FC;min-width:120px;"
            )
            t_lay.addWidget(self._tc_label)
            t_lay.addSpacing(12)

            transport_btns = [
                ("⏮", "Go to Start"),
                ("◀◀", "Rewind"),
                ("▶", "Play/Pause"),
                ("▶▶", "Fast Forward"),
                ("⏭", "Go to End"),
            ]
            self._play_btn: QPushButton | None = None
            for sym, tip in transport_btns:
                btn = QPushButton(sym, transport)
                btn.setFixedSize(34, 34)
                btn.setToolTip(tip)
                btn.setStyleSheet(
                    "QPushButton{background:#1C2431;border:1px solid #283241;"
                    "border-radius:7px;font-size:14px;}"
                    "QPushButton:hover{background:#4F8CFF;border-color:#4F8CFF;}"
                )
                t_lay.addWidget(btn)
                if sym == "▶":
                    self._play_btn = btn

            t_lay.addSpacing(12)

            # Duration label
            dur_lbl = QLabel("/ 02:11:40.000", transport)
            dur_lbl.setStyleSheet("font-family:'Cascadia Code';font-size:13px;color:#687386;")
            t_lay.addWidget(dur_lbl)

            t_lay.addStretch()

            # Audio selector
            for label, tip in [("A", "Original Audio"), ("B", "Dubbed Audio")]:
                ab_btn = QPushButton(label, transport)
                ab_btn.setFixedSize(30, 30)
                ab_btn.setCheckable(True)
                ab_btn.setChecked(label == "B")
                ab_btn.setToolTip(tip)
                ab_btn.setStyleSheet(
                    "QPushButton{background:#1C2431;border:1px solid #283241;"
                    "border-radius:5px;font-weight:700;font-size:12px;}"
                    "QPushButton:checked{background:#1E3A5F;border-color:#4F8CFF;color:#4F8CFF;}"
                )
                t_lay.addWidget(ab_btn)

            # Zoom buttons
            t_lay.addSpacing(12)
            zoom_out_btn = QPushButton("−", transport)
            zoom_out_btn.setFixedSize(28, 28)
            zoom_out_btn.setToolTip("Zoom Out  (−)")
            zoom_out_btn.setStyleSheet(
                "QPushButton{background:#1C2431;border:1px solid #283241;border-radius:5px;font-size:14px;}"
                "QPushButton:hover{background:#283241;}"
            )
            t_lay.addWidget(zoom_out_btn)

            zoom_in_btn = QPushButton("+", transport)
            zoom_in_btn.setFixedSize(28, 28)
            zoom_in_btn.setToolTip("Zoom In  (+)")
            zoom_in_btn.setStyleSheet(
                "QPushButton{background:#1C2431;border:1px solid #283241;border-radius:5px;font-size:14px;}"
                "QPushButton:hover{background:#283241;}"
            )
            t_lay.addWidget(zoom_in_btn)

            root.addWidget(transport)

            # ── Timeline body ──────────────────────────────────────────
            # Quality Heatmap bar (Section 33)
            from aidub.ui.widgets.common import QualityHeatmapWidget  # noqa: PLC0415
            self._heatmap = QualityHeatmapWidget(7940.0, self)
            root.addWidget(self._heatmap)

            timeline_body = QWidget(self)
            timeline_body.setStyleSheet("background:#0D1118;")
            tl_body_lay = QHBoxLayout(timeline_body)
            tl_body_lay.setContentsMargins(0, 0, 0, 0)
            tl_body_lay.setSpacing(0)

            # Track header panel
            self._header_panel = _TrackHeaderPanel(timeline_body)
            tl_body_lay.addWidget(self._header_panel)

            # Graphics scene + view
            self._scene = QGraphicsScene(self)
            self._timeline_view = _TimelineView(self._scene, self._header_panel, timeline_body)
            self._timeline_view.timecode_changed.connect(self._update_timecode)
            self._heatmap.timecode_clicked.connect(self._timeline_view.set_playhead)
            tl_body_lay.addWidget(self._timeline_view, 1)

            root.addWidget(timeline_body, 1)

            # Build the scene
            self._timeline_view.build_scene()

            # Wire buttons
            if self._play_btn:
                self._play_btn.clicked.connect(self._timeline_view.toggle_play)
            zoom_in_btn.clicked.connect(self._timeline_view.zoom_in)
            zoom_out_btn.clicked.connect(self._timeline_view.zoom_out)

        def _update_timecode(self, sec: float) -> None:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec % 1) * 1000)
            self._tc_label.setText(f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}")


__all__ = ["TimelineScreen"]
