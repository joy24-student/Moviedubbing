"""
Media Bin screen — Premiere-style project media browser.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
        QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W

_TREE = {
    "📁 Source": ["movie.mkv"],
    "📁 Audio":  ["original_5.1.wav", "stems_music.wav", "stems_fx.wav"],
    "📁 Subtitles": ["original_en.srt", "original_en.vtt"],
    "📁 Generated / Bengali": ["dub_bn.wav", "subtitles_bn.srt"],
    "📁 Generated / Hindi":   ["dub_hi.wav", "subtitles_hi.srt"],
    "📁 Proxies": ["proxy_1080p.mp4"],
    "📁 Stems": [],
}

_META = {
    "VIDEO": {"Resolution": "3840 × 2160", "FPS": "23.976", "Codec": "HEVC", "Bit Depth": "10-bit", "HDR": "HDR10"},
    "AUDIO": {"Language": "English", "Channels": "5.1", "Sample Rate": "48 kHz", "Bit Depth": "24-bit"},
    "SUBTITLE": {"Language": "English", "Format": "PGS"},
    "DURATION": {"": "02:11:42.683"},
}

if _QT:
    class MediaBinScreen(QWidget):  # type: ignore[misc]
        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            topbar = QFrame(self)
            topbar.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;")
            topbar.setFixedHeight(48)
            tb = QHBoxLayout(topbar)
            tb.setContentsMargins(16, 0, 16, 0)
            t = QLabel("Media", self)
            t.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(t)
            tb.addStretch()
            for label in ["Import…", "Import Folder…"]:
                btn = QPushButton(label, topbar)
                btn.setFixedHeight(34)
                tb.addWidget(btn)
                tb.addSpacing(6)
            root.addWidget(topbar)

            splitter = QSplitter(Qt.Orientation.Horizontal, self)

            # Left: tree
            tree_panel = QWidget()
            tree_panel.setStyleSheet("background:#161D28;")
            tp_lay = QVBoxLayout(tree_panel)
            tp_lay.setContentsMargins(0, 0, 0, 0)
            tp_lay.setSpacing(0)
            hdr = QLabel("  PROJECT MEDIA", tree_panel)
            hdr.setObjectName("SectionLabel")
            hdr.setContentsMargins(12, 10, 12, 8)
            tp_lay.addWidget(hdr)
            tree = QTreeWidget(tree_panel)
            tree.setHeaderHidden(True)
            tree.setStyleSheet(
                "QTreeWidget{background:#161D28;border:none;border-right:1px solid #283241;}"
                "QTreeWidget::item{padding:6px 8px;}"
                "QTreeWidget::item:selected{background:#1E3A5F;}"
            )
            for folder, items in _TREE.items():
                parent_item = QTreeWidgetItem([folder])
                for sub in items:
                    child = QTreeWidgetItem([f"  {sub}"])
                    parent_item.addChild(child)
                parent_item.setExpanded(True)
                tree.addTopLevelItem(parent_item)
            tp_lay.addWidget(tree, 1)
            splitter.addWidget(tree_panel)

            # Right: inspector
            right = QScrollArea()
            right.setWidgetResizable(True)
            right.setFrameShape(QFrame.Shape.NoFrame)
            right.setStyleSheet("background:#0D1118;")
            inner = QWidget()
            inner.setStyleSheet("background:#0D1118;")
            r_lay = QVBoxLayout(inner)
            r_lay.setContentsMargins(20, 16, 20, 16)
            r_lay.setSpacing(16)

            # Thumbnail stub
            thumb = QFrame(inner)
            thumb.setFixedHeight(200)
            thumb.setStyleSheet(
                "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1C2431,stop:1 #080B10);"
                "border:1px solid #283241;border-radius:8px;"
            )
            icon = QLabel("🎬", thumb)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet("font-size:60px;background:transparent;border:none;")
            tl = QVBoxLayout(thumb)
            tl.addWidget(icon)
            r_lay.addWidget(thumb)

            for section, fields in _META.items():
                sec_lbl = QLabel(section, inner)
                sec_lbl.setObjectName("SectionLabel")
                r_lay.addWidget(sec_lbl)
                for k, v in fields.items():
                    row = QHBoxLayout()
                    kl = QLabel(k or section, inner)
                    kl.setObjectName("MetaLabel")
                    kl.setFixedWidth(100)
                    vl = QLabel(v, inner)
                    vl.setObjectName("ValueLabel")
                    row.addWidget(kl)
                    row.addWidget(vl)
                    row.addStretch()
                    r_lay.addLayout(row)

            for label in ["Create Proxy", "Extract Audio", "Extract Subtitle", "Analyze"]:
                btn = QPushButton(label, inner)
                btn.setFixedHeight(34)
                r_lay.addWidget(btn)

            r_lay.addStretch()
            right.setWidget(inner)
            splitter.addWidget(right)
            splitter.setSizes([240, 500])

            root.addWidget(splitter, 1)

__all__ = ["MediaBinScreen"]
