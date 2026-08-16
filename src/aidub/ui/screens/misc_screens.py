"""
Lip-Sync Studio, Provider Manager, Model Manager, Settings — 4 screens.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QCheckBox, QComboBox, QFrame, QGridLayout, QGroupBox,
        QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
        QPushButton, QScrollArea, QSlider, QSplitter,
        QTabWidget, QVBoxLayout, QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


# ─────────────────────────────────────────────────────────────────────────────
# Lip Sync Studio
# ─────────────────────────────────────────────────────────────────────────────
if _QT:
    class LipSyncScreen(QWidget):  # type: ignore[misc]
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
            lbl = QLabel("Lip-Sync Studio", self)
            lbl.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(lbl)
            tb.addStretch()
            root.addWidget(topbar)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 24)
            layout.setSpacing(20)

            # Side-by-side video panes
            video_row = QHBoxLayout()
            video_row.setSpacing(12)
            for label, color in [("ORIGINAL", "#22D3EE"), ("GENERATED", "#4F8CFF")]:
                pane = QFrame(content)
                pane.setFixedHeight(220)
                pane.setStyleSheet(
                    "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1C2431,stop:1 #080B10);"
                    "border:1px solid #283241;border-radius:8px;"
                )
                p_lay = QVBoxLayout(pane)
                p_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
                ico = QLabel("👄", pane)
                ico.setStyleSheet("font-size:52px;background:transparent;border:none;")
                ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
                p_lay.addWidget(ico)
                lbl2 = QLabel(label, pane)
                lbl2.setStyleSheet(f"font-size:11px;font-weight:700;color:{color};background:transparent;border:none;")
                lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
                p_lay.addWidget(lbl2)
                video_row.addWidget(pane, 1)
            layout.addLayout(video_row)

            # Scores
            scores_frame = QFrame(content)
            scores_frame.setObjectName("Panel")
            sf_lay = QGridLayout(scores_frame)
            sf_lay.setContentsMargins(20, 14, 20, 14)
            sf_lay.setSpacing(12)
            scores = [
                ("Lip Sync Score",    "95%",   "#22C55E"),
                ("Active Speaker",    "Tony",   "#4F8CFF"),
                ("Face Confidence",   "98%",   "#22C55E"),
                ("Mouth Visibility",  "91%",   "#22C55E"),
                ("Engine",            "Cinema V2", "#A855F7"),
            ]
            for i, (k, v, color) in enumerate(scores):
                kl = QLabel(k, scores_frame)
                kl.setObjectName("MetaLabel")
                vl = QLabel(v, scores_frame)
                vl.setStyleSheet(f"font-size:14px;font-weight:700;color:{color};")
                sf_lay.addWidget(kl, i, 0)
                sf_lay.addWidget(vl, i, 1)
            layout.addWidget(scores_frame)

            # Controls
            ctrl = QHBoxLayout()
            for label, primary in [("⚡ Fast Preview", False), ("🎬 High Quality Render", True)]:
                btn = QPushButton(label, content)
                btn.setFixedHeight(40)
                if primary:
                    btn.setProperty("primary", "true")
                ctrl.addWidget(btn)
            ctrl.addStretch()
            layout.addLayout(ctrl)
            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Provider Manager
# ─────────────────────────────────────────────────────────────────────────────
_PROVIDERS = [
    ("DeepSeek",  True,  "1.2s", "98%", "#22C55E", "deepseek-chat-v3"),
    ("Gemini",    True,  "0.8s", "99%", "#22C55E", "gemini-2.0-flash"),
    ("ChatGPT",   True,  "1.1s", "99%", "#22C55E", "gpt-4o"),
    ("Local LLM", False, "—",    "—",   "#687386", "llama-3.1-70b"),
]

if _QT:
    class ProviderManagerScreen(QWidget):  # type: ignore[misc]
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
            lbl = QLabel("AI Providers", self)
            lbl.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(lbl)
            tb.addStretch()
            root.addWidget(topbar)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 24)
            layout.setSpacing(14)
            layout.addWidget(self._sec("PROVIDERS"))

            for name, online, latency, success, color, model in _PROVIDERS:
                card = QFrame(content)
                card.setObjectName("Panel")
                c_lay = QVBoxLayout(card)
                c_lay.setContentsMargins(16, 14, 16, 14)
                c_lay.setSpacing(10)

                top = QHBoxLayout()
                indicator = QLabel("●" if online else "○", card)
                indicator.setStyleSheet(f"font-size:16px;color:{color};")
                top.addWidget(indicator)
                name_lbl = QLabel(name, card)
                name_lbl.setStyleSheet("font-size:15px;font-weight:700;")
                top.addWidget(name_lbl)
                top.addStretch()
                status_lbl = QLabel("Online" if online else "Unloaded", card)
                status_lbl.setStyleSheet(f"font-size:12px;color:{color};font-weight:600;")
                top.addWidget(status_lbl)
                c_lay.addLayout(top)

                info_row = QHBoxLayout()
                for label, val in [("Model", model), ("Latency", latency), ("Success", success)]:
                    col = QVBoxLayout()
                    col.setSpacing(2)
                    k = QLabel(label, card)
                    k.setObjectName("MetaLabel")
                    v = QLabel(val, card)
                    v.setObjectName("ValueLabel")
                    col.addWidget(k)
                    col.addWidget(v)
                    info_row.addLayout(col)
                    info_row.addSpacing(24)
                info_row.addStretch()
                c_lay.addLayout(info_row)

                btns = QHBoxLayout()
                for label in ["Test", "Edit Endpoint", "API Key"]:
                    b = QPushButton(label, card)
                    b.setFixedHeight(28)
                    b.setStyleSheet("font-size:11px;")
                    btns.addWidget(b)
                btns.addStretch()
                en_btn = QPushButton("Disable" if online else "Enable", card)
                en_btn.setFixedHeight(28)
                if not online:
                    en_btn.setProperty("accent", "success")
                btns.addWidget(en_btn)
                c_lay.addLayout(btns)
                layout.addWidget(card)

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll, 1)

        @staticmethod
        def _sec(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("SectionLabel")
            return lbl


# ─────────────────────────────────────────────────────────────────────────────
# Model Manager
# ─────────────────────────────────────────────────────────────────────────────
_MODELS = [
    ("Speech Recognition",   "Faster Whisper Large v3", True,  3.1),
    ("Speaker Diarization",  "pyannote 3.1",             True,  1.4),
    ("Voice Engine",         "Local Voice Engine v2",    True,  6.2),
    ("Fast Lip Sync",        "MuseTalk v1.5",            True,  4.8),
    ("Cinema Lip Sync",      "LatentSync v2 4K",         False, 12.3),
    ("Translation LLM",      "Local LLM 70B",            False, 41.2),
    ("Source Separation",    "Demucs v4",                True,  0.8),
]

if _QT:
    class ModelManagerScreen(QWidget):  # type: ignore[misc]
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
            lbl = QLabel("Model Manager", self)
            lbl.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(lbl)
            tb.addStretch()
            root.addWidget(topbar)

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            content = QWidget()
            content.setStyleSheet("background:#0D1118;")
            layout = QVBoxLayout(content)
            layout.setContentsMargins(24, 20, 24, 24)
            layout.setSpacing(10)
            layout.addWidget(self._sec("LOCAL MODELS"))

            for role, name, installed, size_gb in _MODELS:
                card = QFrame(content)
                card.setObjectName("ElevatedPanel")
                card.setStyleSheet("QFrame#ElevatedPanel{background:#1C2431;border:1px solid #283241;border-radius:8px;}")
                c_lay = QHBoxLayout(card)
                c_lay.setContentsMargins(16, 12, 16, 12)
                c_lay.setSpacing(12)

                # Icon
                icon = QLabel("✓" if installed else "○", card)
                icon.setStyleSheet(f"font-size:16px;color:{'#22C55E' if installed else '#687386'};font-weight:700;")
                icon.setFixedWidth(20)
                c_lay.addWidget(icon)

                # Info
                info = QVBoxLayout()
                info.setSpacing(2)
                role_lbl = QLabel(role, card)
                role_lbl.setStyleSheet("font-size:11px;color:#687386;font-weight:600;letter-spacing:0.5px;")
                info.addWidget(role_lbl)
                name_lbl = QLabel(name, card)
                name_lbl.setStyleSheet("font-size:13px;font-weight:600;color:#F7F9FC;")
                info.addWidget(name_lbl)
                c_lay.addLayout(info)
                c_lay.addStretch()

                size_lbl = QLabel(f"{size_gb:.1f} GB", card)
                size_lbl.setStyleSheet("font-size:12px;color:#687386;font-family:'Cascadia Code';min-width:55px;")
                c_lay.addWidget(size_lbl)

                # Action buttons
                if installed:
                    for label, accent in [("Load", ""), ("Unload", ""), ("Delete", "danger")]:
                        b = QPushButton(label, card)
                        b.setFixedHeight(28)
                        b.setStyleSheet("font-size:11px;")
                        if accent:
                            b.setProperty("accent", accent)
                        c_lay.addWidget(b)
                else:
                    b = QPushButton("Install", card)
                    b.setFixedHeight(28)
                    b.setProperty("accent", "success")
                    c_lay.addWidget(b)

                layout.addWidget(card)

            layout.addStretch()
            scroll.setWidget(content)
            root.addWidget(scroll, 1)

        @staticmethod
        def _sec(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("SectionLabel")
            return lbl


# ─────────────────────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────────────────────
_SETTINGS_CATEGORIES = [
    "General", "Appearance", "Language", "Project", "Autosave",
    "Performance", "GPU", "AI Providers", "AI Models", "Translation",
    "Voice", "Lip Sync", "Audio", "Subtitle", "Storage",
    "Cache", "Privacy", "Security", "Shortcuts", "Advanced",
]

if _QT:
    class SettingsScreen(QWidget):  # type: ignore[misc]
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
            lbl = QLabel("Settings", self)
            lbl.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            tb.addWidget(lbl)
            root.addWidget(topbar)

            splitter = QSplitter(Qt.Orientation.Horizontal, self)

            # Category list
            cat_panel = QWidget()
            cat_panel.setStyleSheet("background:#161D28;")
            cat_panel.setFixedWidth(190)
            cp_lay = QVBoxLayout(cat_panel)
            cp_lay.setContentsMargins(0, 8, 0, 8)
            cat_list = QListWidget(cat_panel)
            cat_list.setObjectName("NavList")
            cat_list.setStyleSheet(
                "QListWidget{background:#161D28;border:none;border-right:1px solid #283241;}"
                "QListWidget::item{padding:9px 14px;border-radius:0;margin:0;}"
                "QListWidget::item:selected{background:#1E3A5F;color:#F7F9FC;border:none;}"
            )
            for cat in _SETTINGS_CATEGORIES:
                cat_list.addItem(cat)
            cat_list.setCurrentRow(0)
            cp_lay.addWidget(cat_list)
            splitter.addWidget(cat_panel)

            # Content pane
            right = QScrollArea()
            right.setWidgetResizable(True)
            right.setFrameShape(QFrame.Shape.NoFrame)
            right.setStyleSheet("background:#0D1118;")
            inner = QWidget()
            inner.setStyleSheet("background:#0D1118;")
            r_lay = QVBoxLayout(inner)
            r_lay.setContentsMargins(28, 20, 28, 28)
            r_lay.setSpacing(16)

            # General settings pane
            sec_lbl = QLabel("General", inner)
            sec_lbl.setObjectName("ScreenTitle")
            sec_lbl.setStyleSheet("font-size:22px;font-weight:700;")
            r_lay.addWidget(sec_lbl)

            gen_group = QGroupBox("Application", inner)
            gg_lay = QVBoxLayout(gen_group)
            for setting in [
                ("Check for updates automatically", True),
                ("Restore last project on startup", True),
                ("Show tips on startup", False),
                ("Enable crash reporting (anonymous)", True),
            ]:
                cb = QCheckBox(setting[0], gen_group)
                cb.setChecked(setting[1])
                gg_lay.addWidget(cb)
            r_lay.addWidget(gen_group)

            auto_group = QGroupBox("Autosave", inner)
            a_lay = QVBoxLayout(auto_group)
            from PySide6.QtWidgets import QSpinBox  # noqa: PLC0415
            row = QHBoxLayout()
            row.addWidget(QLabel("Save every", auto_group))
            sb = QSpinBox(auto_group)
            sb.setRange(5, 300)
            sb.setValue(15)
            sb.setSuffix(" seconds")
            row.addWidget(sb)
            row.addStretch()
            a_lay.addLayout(row)
            r_lay.addWidget(auto_group)

            perf_group = QGroupBox("Performance", inner)
            p_lay = QVBoxLayout(perf_group)
            for setting in [
                ("Use GPU acceleration (CUDA)", True),
                ("Enable hardware video decode (NVDEC)", True),
                ("Enable hardware video encode (NVENC)", True),
                ("Auto-manage VRAM", True),
            ]:
                cb = QCheckBox(setting[0], perf_group)
                cb.setChecked(setting[1])
                p_lay.addWidget(cb)
            r_lay.addWidget(perf_group)

            r_lay.addStretch()
            right.setWidget(inner)
            splitter.addWidget(right)
            splitter.setSizes([190, 600])
            root.addWidget(splitter, 1)


__all__ = [
    "ExportScreen",
    "LipSyncScreen",
    "ModelManagerScreen",
    "ProviderManagerScreen",
    "SettingsScreen",
]
