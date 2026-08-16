"""
New Project Wizard — 4-step onboarding flow.

Step 1: Movie drop/browse + metadata preview
Step 2: Language selection (source + multi-select targets)
Step 3: Processing mode cards (Fast / Professional / Cinema / Custom)
Step 4: AI Engine selection
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QButtonGroup,
        QCheckBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSizePolicy,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W

_LANGUAGES = [
    ("বাংলা", "Bengali", "bn"),
    ("हिंदी", "Hindi", "hi"),
    ("தமிழ்", "Tamil", "ta"),
    ("Español", "Spanish", "es"),
    ("Français", "French", "fr"),
    ("Deutsch", "German", "de"),
    ("العربية", "Arabic", "ar"),
    ("日本語", "Japanese", "ja"),
    ("Português", "Portuguese", "pt"),
    ("한국어", "Korean", "ko"),
    ("Italiano", "Italian", "it"),
    ("Русский", "Russian", "ru"),
]

if _QT:

    class _StepIndicator(QWidget):  # type: ignore[misc]
        def __init__(self, steps: list[str], parent: _W | None = None) -> None:
            super().__init__(parent)
            self._steps = steps
            self._current = 0
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            self._circles: list[QLabel] = []
            self._lines: list[QFrame] = []

            for i, step in enumerate(steps):
                col = QVBoxLayout()
                col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                circle = QLabel(str(i + 1), self)
                circle.setFixedSize(32, 32)
                circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
                circle.setStyleSheet(
                    "border-radius: 16px; background: #1C2431; color: #687386; "
                    "font-weight: 700; border: 2px solid #283241;"
                )
                col.addWidget(circle, alignment=Qt.AlignmentFlag.AlignHCenter)
                lbl = QLabel(step, self)
                lbl.setStyleSheet("font-size: 11px; color: #687386;")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                col.addWidget(lbl)
                self._circles.append(circle)

                layout.addLayout(col)
                if i < len(steps) - 1:
                    line = QFrame(self)
                    line.setFrameShape(QFrame.Shape.HLine)
                    line.setFixedHeight(2)
                    line.setSizePolicy(
                        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                    )
                    line.setStyleSheet("background: #283241; margin-bottom: 18px;")
                    layout.addWidget(line)
                    self._lines.append(line)

            self.set_step(0)

        def set_step(self, idx: int) -> None:
            self._current = idx
            for i, circle in enumerate(self._circles):
                if i < idx:
                    circle.setStyleSheet(
                        "border-radius: 16px; background: #4F8CFF; color: #fff; "
                        "font-weight: 700; border: none;"
                    )
                    circle.setText("✓")
                elif i == idx:
                    circle.setStyleSheet(
                        "border-radius: 16px; background: #1C2431; color: #4F8CFF; "
                        "font-weight: 700; border: 2px solid #4F8CFF;"
                    )
                    circle.setText(str(i + 1))
                else:
                    circle.setStyleSheet(
                        "border-radius: 16px; background: #1C2431; color: #687386; "
                        "font-weight: 700; border: 2px solid #283241;"
                    )
                    circle.setText(str(i + 1))

    class _DropZone(QFrame):  # type: ignore[misc]
        file_selected = Signal(str)

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setAcceptDrops(True)
            self.setMinimumHeight(200)
            self.setObjectName("DropZone")
            self.setStyleSheet(
                "QFrame#DropZone{"
                "background:#0D1118;border:2px dashed #34415A;"
                "border-radius:12px;}"
                "QFrame#DropZone:hover{border-color:#4F8CFF;}"
            )
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setSpacing(10)

            icon = QLabel("🎬", self)
            icon.setStyleSheet("font-size: 48px; background: transparent; border: none;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon)

            msg = QLabel("Drop movie file here", self)
            msg.setStyleSheet("font-size: 16px; font-weight: 600; color: #F7F9FC; background:transparent;border:none;")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(msg)

            sub = QLabel("MKV · MP4 · MOV · AVI · M2TS  —  up to 4K HDR", self)
            sub.setStyleSheet("font-size: 12px; color: #687386; background:transparent;border:none;")
            sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(sub)

            browse_btn = QPushButton("Browse…", self)
            browse_btn.setFixedWidth(120)
            browse_btn.clicked.connect(self._browse)
            layout.addWidget(browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            self._path: str = ""

        def _browse(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Movie File", "",
                "Video Files (*.mkv *.mp4 *.mov *.avi *.m2ts *.ts *.webm);;All Files (*)"
            )
            if path:
                self._path = path
                self._show_selected(path)
                self.file_selected.emit(path)

        def _show_selected(self, path: str) -> None:
            import os
            name = os.path.basename(path)
            size_gb = os.path.getsize(path) / 1e9 if os.path.exists(path) else 0
            self.setStyleSheet(
                "QFrame#DropZone{"
                "background:#0D1118;border:2px solid #4F8CFF;"
                "border-radius:12px;}"
            )
            # Clear and rebuild
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            lbl = QLabel(f"✓  {name}\n{size_gb:.1f} GB", self)
            lbl.setStyleSheet(
                "font-size:14px;font-weight:700;color:#22C55E;"
                "background:transparent;border:none;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout().addWidget(lbl)

        def dragEnterEvent(self, event: object) -> None:  # noqa: N802
            if hasattr(event, "mimeData") and event.mimeData().hasUrls():  # type: ignore[attr-defined]
                event.acceptProposedAction()  # type: ignore[attr-defined]

        def dropEvent(self, event: object) -> None:  # noqa: N802
            urls = event.mimeData().urls()  # type: ignore[attr-defined]
            if urls:
                path = urls[0].toLocalFile()
                self._path = path
                self._show_selected(path)
                self.file_selected.emit(path)

    class _ModeCard(QFrame):  # type: ignore[misc]
        def __init__(
            self,
            icon: str,
            title: str,
            desc: str,
            recommended: bool = False,
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("Card")
            self.setFixedSize(175, 155)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self._selected = False
            self._recommended = recommended

            layout = QVBoxLayout(self)
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(8)

            icon_lbl = QLabel(icon, self)
            icon_lbl.setStyleSheet("font-size: 28px; background: transparent; border:none;")
            layout.addWidget(icon_lbl)

            top_row = QHBoxLayout()
            title_lbl = QLabel(title, self)
            title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #F7F9FC;")
            top_row.addWidget(title_lbl)
            if recommended:
                badge = QLabel("★", self)
                badge.setStyleSheet("font-size: 12px; color: #F59E0B;")
                top_row.addWidget(badge)
            top_row.addStretch()
            layout.addLayout(top_row)

            desc_lbl = QLabel(desc, self)
            desc_lbl.setStyleSheet("font-size: 11px; color: #687386;")
            desc_lbl.setWordWrap(True)
            layout.addWidget(desc_lbl)

        def set_selected(self, selected: bool) -> None:
            self._selected = selected
            border = "#4F8CFF" if selected else "#283241"
            bg = "#1E3A5F" if selected else "#161D28"
            self.setStyleSheet(
                f"QFrame#Card{{background:{bg};border:2px solid {border};border-radius:10px;}}"
            )

        def mousePressEvent(self, _event: object) -> None:  # noqa: N802
            self.set_selected(True)

    # ------------------------------------------------------------------
    # Project Wizard
    # ------------------------------------------------------------------
    class ProjectWizardScreen(QWidget):  # type: ignore[misc]
        """New Project Wizard — 4-step onboarding."""

        project_created = Signal(dict)
        cancelled = Signal()

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self._step = 0
            self._movie_path = ""
            self._target_langs: list[str] = ["bn", "hi"]
            self._mode = "professional"
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            # Header bar
            header = QFrame(self)
            header.setObjectName("Panel")
            header.setStyleSheet("background:#0D1118;border-bottom:1px solid #283241;border-radius:0;")
            header.setFixedHeight(52)
            h_layout = QHBoxLayout(header)
            h_layout.setContentsMargins(24, 0, 24, 0)
            title_lbl = QLabel("New Project", self)
            title_lbl.setObjectName("ScreenTitle")
            title_lbl.setStyleSheet("font-size: 18px; font-weight: 700;")
            h_layout.addWidget(title_lbl)
            h_layout.addStretch()
            cancel_btn = QPushButton("Cancel", self)
            cancel_btn.clicked.connect(self.cancelled)
            h_layout.addWidget(cancel_btn)
            root.addWidget(header)

            # Step indicator
            steps = ["Movie", "Languages", "Mode", "AI Engine"]
            self._step_indicator = _StepIndicator(steps, self)
            self._step_indicator.setFixedHeight(72)
            step_wrapper = QFrame(self)
            step_wrapper.setStyleSheet("background:#161D28;border-bottom:1px solid #283241;")
            sw_layout = QHBoxLayout(step_wrapper)
            sw_layout.setContentsMargins(60, 8, 60, 8)
            sw_layout.addWidget(self._step_indicator)
            root.addWidget(step_wrapper)

            # Stacked content
            self._stack = QStackedWidget(self)
            self._stack.addWidget(self._build_step1())
            self._stack.addWidget(self._build_step2())
            self._stack.addWidget(self._build_step3())
            self._stack.addWidget(self._build_step4())
            root.addWidget(self._stack, 1)

            # Navigation buttons
            nav_bar = QFrame(self)
            nav_bar.setStyleSheet("background:#0D1118;border-top:1px solid #283241;")
            nav_bar.setFixedHeight(60)
            nav_layout = QHBoxLayout(nav_bar)
            nav_layout.setContentsMargins(24, 0, 24, 0)
            self._back_btn = QPushButton("← Back", self)
            self._back_btn.setEnabled(False)
            self._back_btn.clicked.connect(self._go_back)
            nav_layout.addWidget(self._back_btn)
            nav_layout.addStretch()
            self._next_btn = QPushButton("Next →", self)
            self._next_btn.setProperty("primary", "true")
            self._next_btn.clicked.connect(self._go_next)
            nav_layout.addWidget(self._next_btn)
            root.addWidget(nav_bar)

        # -------- Step 1: Movie --------
        def _build_step1(self) -> QWidget:
            w = QWidget()
            layout = QVBoxLayout(w)
            layout.setContentsMargins(60, 40, 60, 40)
            layout.setSpacing(20)

            layout.addWidget(QLabel("Select Movie File", w))

            self._drop_zone = _DropZone(w)
            self._drop_zone.file_selected.connect(self._on_movie_selected)
            layout.addWidget(self._drop_zone)

            # Metadata panel (hidden until file selected)
            self._meta_panel = QFrame(w)
            self._meta_panel.setObjectName("Panel")
            self._meta_panel.hide()
            meta_layout = QGridLayout(self._meta_panel)
            meta_layout.setContentsMargins(16, 14, 16, 14)
            meta_layout.setSpacing(8)
            self._meta_labels: dict[str, QLabel] = {}
            rows = [
                ("Movie Name", "—"), ("Duration", "—"), ("Resolution", "—"),
                ("FPS", "—"), ("Video Codec", "—"), ("Audio", "—"),
                ("Subtitles", "—"), ("File Size", "—"),
            ]
            for i, (key, val) in enumerate(rows):
                k_lbl = QLabel(key + ":", w)
                k_lbl.setObjectName("MetaLabel")
                v_lbl = QLabel(val, w)
                v_lbl.setObjectName("ValueLabel")
                meta_layout.addWidget(k_lbl, i, 0)
                meta_layout.addWidget(v_lbl, i, 1)
                self._meta_labels[key] = v_lbl
            layout.addWidget(self._meta_panel)
            layout.addStretch()
            return w

        def _on_movie_selected(self, path: str) -> None:
            import os
            self._movie_path = path
            name = os.path.basename(path)
            size_gb = os.path.getsize(path) / 1e9 if os.path.exists(path) else 0
            self._meta_labels["Movie Name"].setText(name)
            self._meta_labels["Duration"].setText("02:11:42")
            self._meta_labels["Resolution"].setText("3840 × 2160")
            self._meta_labels["FPS"].setText("23.976")
            self._meta_labels["Video Codec"].setText("HEVC / H.265 10-bit")
            self._meta_labels["Audio"].setText("English 5.1  48 kHz 24-bit")
            self._meta_labels["Subtitles"].setText("English (PGS)")
            self._meta_labels["File Size"].setText(f"{size_gb:.1f} GB")
            self._meta_panel.show()

        # -------- Step 2: Languages --------
        def _build_step2(self) -> QWidget:
            w = QWidget()
            layout = QVBoxLayout(w)
            layout.setContentsMargins(60, 30, 60, 30)
            layout.setSpacing(16)
            layout.addWidget(QLabel("Target Languages", w))

            scroll = QScrollArea(w)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            inner = QWidget()
            grid = QGridLayout(inner)
            grid.setSpacing(10)
            self._lang_checks: dict[str, QCheckBox] = {}
            for i, (native, english, code) in enumerate(_LANGUAGES):
                cb = QCheckBox(f"{native}  {english}", inner)
                cb.setChecked(code in self._target_langs)
                cb.toggled.connect(lambda checked, c=code: self._toggle_lang(c, checked))
                grid.addWidget(cb, i // 3, i % 3)
                self._lang_checks[code] = cb
            scroll.setWidget(inner)
            layout.addWidget(scroll, 1)
            return w

        def _toggle_lang(self, code: str, checked: bool) -> None:
            if checked and code not in self._target_langs:
                self._target_langs.append(code)
            elif not checked and code in self._target_langs:
                self._target_langs.remove(code)

        # -------- Step 3: Processing Mode --------
        def _build_step3(self) -> QWidget:
            w = QWidget()
            layout = QVBoxLayout(w)
            layout.setContentsMargins(60, 30, 60, 30)
            layout.setSpacing(16)
            layout.addWidget(QLabel("Processing Mode", w))

            modes = [
                ("⚡", "FAST", "Quick dubbing\nNo lip sync", False, "fast"),
                ("⭐", "PROFESSIONAL", "Voice • Emotion\nTiming • Lip Sync", True, "professional"),
                ("🎬", "CINEMA", "Maximum quality\nFull mastering\nAdvanced QC", False, "cinema"),
                ("⚙", "CUSTOM", "Choose everything\nmanually", False, "custom"),
            ]

            cards_row = QHBoxLayout()
            cards_row.setSpacing(14)
            self._mode_cards: dict[str, _ModeCard] = {}
            for icon, title, desc, rec, key in modes:
                card = _ModeCard(icon, title, desc, rec, w)
                card.mousePressEvent = lambda e, k=key: self._select_mode(k)  # type: ignore[method-assign]
                cards_row.addWidget(card)
                self._mode_cards[key] = card
            cards_row.addStretch()
            layout.addLayout(cards_row)

            self._select_mode("professional")
            layout.addStretch()
            return w

        def _select_mode(self, key: str) -> None:
            self._mode = key
            for k, card in self._mode_cards.items():
                card.set_selected(k == key)

        # -------- Step 4: AI Engine --------
        def _build_step4(self) -> QWidget:
            w = QWidget()
            layout = QVBoxLayout(w)
            layout.setContentsMargins(60, 30, 60, 30)
            layout.setSpacing(16)
            layout.addWidget(QLabel("AI Engine Selection", w))

            options = [
                ("● Automatic (Recommended)",
                 "Uses the best available engine for each task"),
                ("○ Fully Local",
                 "All processing stays on device — no internet required"),
                ("○ Hybrid",
                 "Local for inference, cloud for translation and QC"),
                ("○ Cloud Preferred",
                 "Highest quality, requires internet connection"),
            ]

            self._engine_group = QButtonGroup(w)
            for i, (label, desc) in enumerate(options):
                radio = QRadioButton(label, w)
                radio.setChecked(i == 0)
                self._engine_group.addButton(radio, i)
                layout.addWidget(radio)
                desc_lbl = QLabel(f"    {desc}", w)
                desc_lbl.setObjectName("MetaLabel")
                layout.addWidget(desc_lbl)
                layout.addSpacing(6)

            layout.addStretch()
            return w

        # -------- Navigation --------
        def _go_back(self) -> None:
            if self._step > 0:
                self._step -= 1
                self._stack.setCurrentIndex(self._step)
                self._step_indicator.set_step(self._step)
                self._back_btn.setEnabled(self._step > 0)
                self._next_btn.setText("Next →")
                self._next_btn.setEnabled(True)

        def _go_next(self) -> None:
            if self._step < 3:
                self._step += 1
                self._stack.setCurrentIndex(self._step)
                self._step_indicator.set_step(self._step)
                self._back_btn.setEnabled(True)
                if self._step == 3:
                    self._next_btn.setText("🚀  Create Project")
            else:
                self._create_project()

        def _create_project(self) -> None:
            self.project_created.emit({
                "movie_path": self._movie_path,
                "target_languages": list(self._target_langs),
                "mode": self._mode,
            })


__all__ = ["ProjectWizardScreen"]
