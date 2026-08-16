"""
AI Movie Dubbing Studio — Professional Main Window.

Full professional post-production shell:
  • Top bar: project name, GPU monitor button, autosave, privacy
  • Collapsible sidebar: 13 production screens + 3 settings screens
  • QStackedWidget: all screens loaded and wired
  • Status bar: GPU%, VRAM, RAM, job count

Preserves full backward compatibility with AIDubMainWindow (legacy shell).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMenu,
        QMenuBar,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QStackedWidget,
        QStatusBar,
        QSystemTrayIcon,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W

# ─────────────────────────────────────────────────────────────────────────────
# Navigation definition
# Each entry: (icon, label, screen_key, shortcut)
# ─────────────────────────────────────────────────────────────────────────────
_NAV_MAIN = [
    ("🏠", "Dashboard",     "dashboard",    "Alt+1"),
    ("🎬", "Media",         "media",        "Alt+2"),
    ("🧠", "Analysis",      "analysis",     "Alt+3"),
    ("🌄", "Scenes",        "scenes",       ""),
    ("👥", "Characters",    "characters",   "Alt+4"),
    ("🌐", "Translation",   "translation",  "Alt+5"),
    ("🎙", "Voice Studio",  "voice",        "Alt+6"),
    ("🎞", "Timeline",      "timeline",     "Alt+7"),
    ("👄", "Lip Sync",      "lipsync",      "Alt+8"),
    ("🎚", "Mixer",         "mixer",        "Alt+9"),
    ("💬", "Subtitles",     "subtitles",    "Alt+0"),
    ("✅", "Quality Control","qc",          ""),
    ("🚀", "Render Queue",  "render",       ""),
    ("📤", "Export",        "export",       ""),
]

_NAV_BOTTOM = [
    ("📖", "Pronunciation", "pronunciation", ""),
    ("📜", "Voice Rights",  "voice_rights",  ""),
    ("🕒", "Versions",      "versions",      ""),
    ("🌐", "Multi-Lang",    "multilang",     ""),
    ("🛠️", "Diagnostics",   "diagnostics",   ""),
    ("🤖", "Models",       "models",        ""),
    ("🔌", "Providers",    "providers",     ""),
    ("⚙",  "Settings",     "settings",      "Ctrl+,"),
]


if _QT:

    # ─────────────────────────────────────────────────────────────────────
    # Top Bar
    # ─────────────────────────────────────────────────────────────────────
    class _TopBar(QFrame):  # type: ignore[misc]
        """Full-width top bar: logo · project name · spacer · GPU · status."""

        gpu_clicked = Signal()
        new_project_clicked = Signal()
        workspace_preset_changed = Signal(str)

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("TopBar")
            self.setFixedHeight(46)

            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 0, 10, 0)
            layout.setSpacing(6)

            # Logo
            logo = QLabel("🎬", self)
            logo.setStyleSheet("font-size:18px;background:transparent;border:none;")
            layout.addWidget(logo)

            # App name
            app_name = QLabel("AI DUBBING STUDIO", self)
            app_name.setObjectName("AppTitle")
            layout.addWidget(app_name)

            # Divider
            div = QFrame(self)
            div.setObjectName("DividerV")
            div.setFixedHeight(18)
            layout.addWidget(div)

            # Project name
            self._project_lbl = QLabel("Avengers Bengali Dub", self)
            self._project_lbl.setObjectName("ProjectName")
            layout.addWidget(self._project_lbl)

            # Status badge
            self._status_badge = QLabel("● Unsaved", self)
            self._status_badge.setObjectName("StatusBadge")
            self._status_badge.setProperty("tone", "warn")
            layout.addWidget(self._status_badge)

            layout.addSpacing(12)

            # Workspace preset selector (Master Spec Section 74 & 75)
            ws_lbl = QLabel("Workspace:", self)
            ws_lbl.setStyleSheet("font-size:11px;color:#A9B2C3;font-weight:600;")
            layout.addWidget(ws_lbl)

            self._ws_combo = QComboBox(self)
            self._ws_combo.addItems([
                "🎞 Editing Workspace",
                "🎙 Dubbing Workspace",
                "🎚 Audio Mixing Workspace",
                "✅ QC & Subtitles Workspace",
            ])
            self._ws_combo.setStyleSheet("QComboBox{background:#161D28;color:#F7F9FC;border:1px solid #283241;padding:2px 8px;border-radius:4px;}")
            self._ws_combo.currentIndexChanged.connect(self._on_ws_changed)
            layout.addWidget(self._ws_combo)

            layout.addStretch()

            # Save indicator
            self._autosave_lbl = QLabel("Autosaved 0s ago", self)
            self._autosave_lbl.setObjectName("TopBarMeta")
            layout.addWidget(self._autosave_lbl)

            layout.addSpacing(8)

            # GPU button
            self._gpu_btn = QPushButton("🖥  RTX 4070  43%", self)
            self._gpu_btn.setObjectName("GpuBtn")
            self._gpu_btn.setFixedHeight(28)
            self._gpu_btn.clicked.connect(self._on_gpu_clicked)
            layout.addWidget(self._gpu_btn)

            # RAM label
            self._ram_lbl = QLabel("RAM 18 GB", self)
            self._ram_lbl.setObjectName("TopBarMeta")
            layout.addWidget(self._ram_lbl)

            # Privacy badge
            priv = QLabel("🔒 Local", self)
            priv.setObjectName("StatusBadge")
            priv.setProperty("tone", "safe")
            layout.addWidget(priv)

            # Notif btn
            notif_btn = QPushButton("🔔", self)
            notif_btn.setObjectName("TopBarBtn")
            notif_btn.setFixedSize(34, 34)
            layout.addWidget(notif_btn)

            # GPU popover (lazy created)
            self._gpu_popover: QWidget | None = None

            # Autosave timer simulation
            self._autosave_counter = 0
            timer = QTimer(self)
            timer.timeout.connect(self._tick_autosave)
            timer.start(1000)

            # GPU % simulation
            gpu_timer = QTimer(self)
            gpu_timer.timeout.connect(self._tick_gpu)
            gpu_timer.start(3000)
            self._gpu_pct = 43

        def set_project(self, name: str) -> None:
            self._project_lbl.setText(name)

        def _on_ws_changed(self, idx: int) -> None:
            presets = ["editing", "dubbing", "audio_mixing", "qc"]
            if 0 <= idx < len(presets):
                self.workspace_preset_changed.emit(presets[idx])

        def set_saved(self, saved: bool) -> None:
            if saved:
                self._status_badge.setText("● Saved")
                self._status_badge.setProperty("tone", "safe")
            else:
                self._status_badge.setText("● Unsaved")
                self._status_badge.setProperty("tone", "warn")
            self._status_badge.style().unpolish(self._status_badge)
            self._status_badge.style().polish(self._status_badge)

        def _tick_autosave(self) -> None:
            self._autosave_counter += 1
            if self._autosave_counter < 60:
                self._autosave_lbl.setText(f"Autosaved {self._autosave_counter}s ago")
            else:
                m = self._autosave_counter // 60
                self._autosave_lbl.setText(f"Autosaved {m}m ago")

        def _tick_gpu(self) -> None:
            import random  # noqa: PLC0415
            self._gpu_pct = max(10, min(99, self._gpu_pct + random.randint(-8, 8)))
            self._gpu_btn.setText(f"🖥  RTX 4070  {self._gpu_pct}%")

        def _on_gpu_clicked(self) -> None:
            from aidub.ui.widgets.common import GpuPopover  # noqa: PLC0415
            if self._gpu_popover is None:
                self._gpu_popover = GpuPopover(self.window())
            pos = self._gpu_btn.mapToGlobal(self._gpu_btn.rect().bottomLeft())
            self._gpu_popover.show_below(pos)  # type: ignore[attr-defined]
            self.gpu_clicked.emit()

    # ─────────────────────────────────────────────────────────────────────
    # Sidebar Navigation
    # ─────────────────────────────────────────────────────────────────────
    class _Sidebar(QFrame):  # type: ignore[misc]
        """Collapsible sidebar navigation with 13+3 items."""

        navigated = Signal(int)

        _COLLAPSED_W = 52
        _EXPANDED_W = 220

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("Sidebar")
            self._expanded = True
            self._all_items = _NAV_MAIN + _NAV_BOTTOM
            self._build_ui()
            self._set_width(self._EXPANDED_W)

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Collapse toggle button
            toggle_row = QFrame(self)
            toggle_row.setStyleSheet("background:transparent;border:none;")
            toggle_row.setFixedHeight(42)
            tr_lay = QHBoxLayout(toggle_row)
            tr_lay.setContentsMargins(8, 0, 8, 0)
            self._brand_lbl = QLabel("WORKSPACE", self)
            self._brand_lbl.setObjectName("SidebarBrand")
            tr_lay.addWidget(self._brand_lbl)
            tr_lay.addStretch()
            self._toggle_btn = QPushButton("◀", self)
            self._toggle_btn.setObjectName("SidebarCollapseBtn")
            self._toggle_btn.clicked.connect(self._toggle)
            tr_lay.addWidget(self._toggle_btn)
            layout.addWidget(toggle_row)

            # Main nav list
            self._nav_list = QListWidget(self)
            self._nav_list.setObjectName("NavList")
            for icon, label, _key, _sc in _NAV_MAIN:
                item = QListWidgetItem(f"  {icon}  {label}")
                self._nav_list.addItem(item)
            self._nav_list.currentRowChanged.connect(self._on_nav_changed)
            layout.addWidget(self._nav_list, 1)

            # Separator
            sep = QFrame(self)
            sep.setObjectName("DividerH")
            layout.addWidget(sep)

            # Bottom nav list
            self._bottom_list = QListWidget(self)
            self._bottom_list.setObjectName("NavList")
            self._bottom_list.setFixedHeight(len(_NAV_BOTTOM) * 44 + 8)
            for icon, label, _key, _sc in _NAV_BOTTOM:
                item = QListWidgetItem(f"  {icon}  {label}")
                self._bottom_list.addItem(item)
            self._bottom_list.currentRowChanged.connect(self._on_bottom_nav_changed)
            layout.addWidget(self._bottom_list)

        def _set_width(self, w: int) -> None:
            self.setFixedWidth(w)

        def _toggle(self) -> None:
            self._expanded = not self._expanded
            if self._expanded:
                self._set_width(self._EXPANDED_W)
                self._toggle_btn.setText("◀")
                self._brand_lbl.show()
                for i in range(self._nav_list.count()):
                    icon, label, _, _ = _NAV_MAIN[i]
                    self._nav_list.item(i).setText(f"  {icon}  {label}")
                for i in range(self._bottom_list.count()):
                    icon, label, _, _ = _NAV_BOTTOM[i]
                    self._bottom_list.item(i).setText(f"  {icon}  {label}")
            else:
                self._set_width(self._COLLAPSED_W)
                self._toggle_btn.setText("▶")
                self._brand_lbl.hide()
                for i in range(self._nav_list.count()):
                    icon = _NAV_MAIN[i][0]
                    self._nav_list.item(i).setText(f" {icon}")
                for i in range(self._bottom_list.count()):
                    icon = _NAV_BOTTOM[i][0]
                    self._bottom_list.item(i).setText(f" {icon}")

        def _on_nav_changed(self, row: int) -> None:
            if row >= 0:
                self._bottom_list.clearSelection()
                self.navigated.emit(row)

        def _on_bottom_nav_changed(self, row: int) -> None:
            if row >= 0:
                self._nav_list.clearSelection()
                self.navigated.emit(len(_NAV_MAIN) + row)

        def select(self, idx: int) -> None:
            """Programmatically select a screen by global index."""
            if idx < len(_NAV_MAIN):
                self._nav_list.setCurrentRow(idx)
            else:
                self._bottom_list.setCurrentRow(idx - len(_NAV_MAIN))

    # ─────────────────────────────────────────────────────────────────────
    # Studio Status Bar
    # ─────────────────────────────────────────────────────────────────────
    class _StudioStatusBar(QStatusBar):  # type: ignore[misc]
        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("StudioStatusBar")

            self._project_lbl = QLabel("Avengers Bengali Dub", self)
            self._project_lbl.setObjectName("StatusBarLabel")
            self.addWidget(self._project_lbl)

            self._jobs_lbl = QLabel("Jobs: 3", self)
            self._jobs_lbl.setObjectName("StatusBarLabel")
            self.addWidget(self._jobs_lbl)

            self.addPermanentWidget(QLabel("", self))

            self._gpu_stat = QLabel("🖥 RTX 4070  43%", self)
            self._gpu_stat.setObjectName("StatusBarLabel")
            self.addPermanentWidget(self._gpu_stat)

            self._vram_stat = QLabel("VRAM  6.8/12 GB", self)
            self._vram_stat.setObjectName("StatusBarLabel")
            self.addPermanentWidget(self._vram_stat)

            self._ram_stat = QLabel("RAM  18/32 GB", self)
            self._ram_stat.setObjectName("StatusBarLabel")
            self.addPermanentWidget(self._ram_stat)

            self._autosave_lbl = QLabel("● Autosaved", self)
            self._autosave_lbl.setObjectName("AutosaveLabel")
            self.addPermanentWidget(self._autosave_lbl)

    # ─────────────────────────────────────────────────────────────────────
    # Main Studio Window
    # ─────────────────────────────────────────────────────────────────────
    class AIDubStudioWindow(QMainWindow):  # type: ignore[misc]
        """
        Full professional AI Movie Dubbing Studio main window.

        Provides:
        - Professional top bar (GPU monitor, autosave, project name)
        - Collapsible sidebar (13 production + 3 settings screens)
        - Lazy-loaded screen stack
        - Keyboard shortcuts for all screens
        - Cmd+K command palette (via parent)
        """

        screen_changed = Signal(str)

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("AIDubStudioWindow")
            self.setWindowTitle("AI Movie Dubbing Studio")
            self.resize(1440, 900)
            self.setMinimumSize(1100, 700)
            self.setDockNestingEnabled(True)

            self._screens: dict[str, QWidget] = {}
            self._current_key = ""

            self._build_ui()
            self._build_menu_bar()
            self._build_system_tray()
            self._build_shortcuts()
            self._navigate_to("dashboard")

        def _build_ui(self) -> None:
            # Apply styles
            from aidub.ui.styles import APPLICATION_STYLE  # noqa: PLC0415
            QApplication.instance().setStyleSheet(APPLICATION_STYLE)  # type: ignore[union-attr]

            central = QWidget(self)
            root = QVBoxLayout(central)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            # Top bar
            self._top_bar = _TopBar(central)
            self._top_bar.workspace_preset_changed.connect(self._on_workspace_preset_changed)
            root.addWidget(self._top_bar)

            # Body: sidebar + stack
            body = QWidget(central)
            body_layout = QHBoxLayout(body)
            body_layout.setContentsMargins(0, 0, 0, 0)
            body_layout.setSpacing(0)

            self._sidebar = _Sidebar(body)
            self._sidebar.navigated.connect(self._on_sidebar_nav)
            body_layout.addWidget(self._sidebar)

            # Main content stack
            self._stack = QStackedWidget(body)
            self._stack.setStyleSheet("QStackedWidget{background:#0D1118;}")
            body_layout.addWidget(self._stack, 1)

            root.addWidget(body, 1)
            self.setCentralWidget(central)

            # Status bar
            self._status_bar = _StudioStatusBar(self)
            self.setStatusBar(self._status_bar)

        def _build_menu_bar(self) -> None:
            """Build native NLE Menu Bar (Section 4.2)."""
            mb = self.menuBar()
            mb.setStyleSheet("QMenuBar{background:#080B10;color:#F7F9FC;} QMenuBar::item:selected{background:#1C2431;}")

            # File
            file_m = mb.addMenu("File")
            file_m.addAction("New Project…", lambda: self._navigate_to("wizard"), QKeySequence("Ctrl+N"))
            file_m.addAction("Open Project…", lambda: self._navigate_to("dashboard"), QKeySequence("Ctrl+O"))
            file_m.addSeparator()
            file_m.addAction("Save Project", lambda: self._top_bar.set_saved(True), QKeySequence("Ctrl+S"))
            file_m.addAction("Export Movie…", lambda: self._navigate_to("export"), QKeySequence("Ctrl+E"))
            file_m.addSeparator()
            file_m.addAction("Exit", self.close)

            # Edit
            edit_m = mb.addMenu("Edit")
            edit_m.addAction("Undo", lambda: None, QKeySequence("Ctrl+Z"))
            edit_m.addAction("Redo", lambda: None, QKeySequence("Ctrl+Y"))
            edit_m.addSeparator()
            edit_m.addAction("Command Palette…", lambda: self._open_cmd_palette(), QKeySequence("Ctrl+Shift+P"))
            edit_m.addAction("Keyboard Shortcuts…", lambda: self._navigate_to("settings"), QKeySequence("Ctrl+K"))

            # View
            view_m = mb.addMenu("View")
            view_m.addAction("Toggle Fullscreen", lambda: self.setWindowState(self.windowState() ^ Qt.WindowState.WindowFullScreen), QKeySequence("F11"))

            # Project
            proj_m = mb.addMenu("Project")
            for icon, label, key, _ in _NAV_MAIN:
                proj_m.addAction(f"{icon} {label}", lambda _=False, k=key: self._navigate_to(k))

            # AI
            ai_m = mb.addMenu("AI")
            ai_m.addAction("🤖 AI Fix All…", lambda: self._open_ai_fix())
            ai_m.addAction("🎙 Regenerate Selected Voice", lambda: self._navigate_to("voice"))
            ai_m.addAction("⏱ Auto-Align Timing", lambda: self._navigate_to("timeline"))

            # Audio
            aud_m = mb.addMenu("Audio")
            aud_m.addAction("🎚 Open Audio Mixer", lambda: self._navigate_to("mixer"))
            aud_m.addAction("🔊 Loudness Check (-23 LUFS)", lambda: self._navigate_to("mixer"))

            # Subtitle
            sub_m = mb.addMenu("Subtitle")
            sub_m.addAction("💬 Subtitle Studio", lambda: self._navigate_to("subtitles"))
            sub_m.addAction("📖 Pronunciation Dictionary", lambda: self._navigate_to("pronunciation"))

            # Render
            rnd_m = mb.addMenu("Render")
            rnd_m.addAction("🚀 Render Queue", lambda: self._navigate_to("render"))

            # Window & Help
            win_m = mb.addMenu("Window")
            win_m.addAction("Dashboard", lambda: self._navigate_to("dashboard"))
            help_m = mb.addMenu("Help")
            help_m.addAction("About Studio", lambda: QMessageBox.about(self, "About AI Movie Dubbing Studio", "AI Movie Dubbing Studio v2.0\nProfessional Localization Workstation"))

        def _build_system_tray(self) -> None:
            """Build System Tray Icon & Context Menu (Section 48)."""
            self._tray = QSystemTrayIcon(self)
            self._tray.setToolTip("AI Movie Dubbing Studio — Active")
            tray_menu = QMenu(self)
            tray_menu.addAction("🎬 Open Studio Window", self.showNormal)
            tray_menu.addAction("⚡ Active Jobs (3)", lambda: self._navigate_to("render"))
            tray_menu.addAction("🖥 GPU Status", lambda: self._navigate_to("models"))
            tray_menu.addSeparator()
            tray_menu.addAction("Exit Studio", self.close)
            self._tray.setContextMenu(tray_menu)
            self._tray.show()

        def _open_cmd_palette(self) -> None:
            from aidub.ui.command_palette import CommandPalette  # noqa: PLC0415
            CommandPalette(self).exec()

        def _open_ai_fix(self) -> None:
            from aidub.ui.dialogs.ai_fix_dialog import AiFixAllDialog  # noqa: PLC0415
            AiFixAllDialog(4, 18, self).exec()

        def _on_workspace_preset_changed(self, preset: str) -> None:
            mapping = {
                "editing": "timeline",
                "dubbing": "translation",
                "audio_mixing": "mixer",
                "qc": "qc",
            }
            target = mapping.get(preset, "dashboard")
            self._navigate_to(target)

        def _build_shortcuts(self) -> None:
            """Wire keyboard shortcuts for all nav items."""
            all_nav = _NAV_MAIN + _NAV_BOTTOM
            for i, (_, _, key, shortcut) in enumerate(all_nav):
                if shortcut:
                    action = QAction(self)
                    action.setShortcut(QKeySequence(shortcut))
                    action.triggered.connect(lambda _=False, k=key: self._navigate_to(k))
                    self.addAction(action)

        def _on_sidebar_nav(self, idx: int) -> None:
            all_nav = _NAV_MAIN + _NAV_BOTTOM
            if 0 <= idx < len(all_nav):
                key = all_nav[idx][2]
                self._navigate_to(key)

        def _navigate_to(self, key: str) -> None:
            if key == self._current_key:
                return
            self._current_key = key

            if key not in self._screens:
                self._screens[key] = self._create_screen(key)
                self._stack.addWidget(self._screens[key])

            self._stack.setCurrentWidget(self._screens[key])
            self.screen_changed.emit(key)

            # Update sidebar selection
            all_nav = _NAV_MAIN + _NAV_BOTTOM
            for i, (_, _, nav_key, _) in enumerate(all_nav):
                if nav_key == key:
                    self._sidebar.select(i)
                    break

        def _create_screen(self, key: str) -> QWidget:
            """Lazy-load and return the screen widget for the given key."""
            try:
                if key == "dashboard":
                    from aidub.ui.screens.dashboard import DashboardScreen  # noqa: PLC0415
                    s = DashboardScreen()
                    s.new_project_requested.connect(lambda: self._navigate_to("wizard"))
                    return s

                if key == "media":
                    from aidub.ui.screens.media_bin import MediaBinScreen  # noqa: PLC0415
                    return MediaBinScreen()

                if key == "analysis":
                    from aidub.ui.screens.analysis import AnalysisScreen  # noqa: PLC0415
                    return AnalysisScreen()

                if key == "scenes":
                    from aidub.ui.screens.scenes import SceneBrowserScreen  # noqa: PLC0415
                    return SceneBrowserScreen()

                if key == "characters":
                    from aidub.ui.screens.characters import CharacterStudioScreen  # noqa: PLC0415
                    return CharacterStudioScreen()

                if key == "translation":
                    from aidub.ui.screens.translation import TranslationScreen  # noqa: PLC0415
                    return TranslationScreen()

                if key == "voice":
                    from aidub.ui.screens.voice_studio import VoiceStudioScreen  # noqa: PLC0415
                    return VoiceStudioScreen()

                if key == "timeline":
                    from aidub.ui.screens.timeline_editor import TimelineScreen  # noqa: PLC0415
                    return TimelineScreen()

                if key == "lipsync":
                    from aidub.ui.screens.misc_screens import LipSyncScreen  # noqa: PLC0415
                    return LipSyncScreen()

                if key == "mixer":
                    from aidub.ui.screens.mixer_screen import MixerScreen  # noqa: PLC0415
                    return MixerScreen()

                if key == "subtitles":
                    from aidub.ui.screens.subtitles import SubtitleStudioScreen  # noqa: PLC0415
                    return SubtitleStudioScreen()

                if key == "pronunciation":
                    from aidub.ui.screens.pronunciation import PronunciationStudioScreen  # noqa: PLC0415
                    return PronunciationStudioScreen()

                if key == "voice_rights":
                    from aidub.ui.screens.voice_rights import VoiceRightsScreen  # noqa: PLC0415
                    return VoiceRightsScreen()

                if key == "versions":
                    from aidub.ui.screens.version_history import VersionHistoryScreen  # noqa: PLC0415
                    return VersionHistoryScreen()

                if key == "multilang":
                    from aidub.ui.screens.multilang_compare import MultiLangCompareScreen  # noqa: PLC0415
                    return MultiLangCompareScreen()

                if key == "diagnostics":
                    from aidub.ui.screens.diagnostics import DiagnosticsScreen  # noqa: PLC0415
                    return DiagnosticsScreen()

                if key == "qc":
                    from aidub.ui.screens.qc_center import QualityControlScreen  # noqa: PLC0415
                    return QualityControlScreen()

                if key == "render":
                    from aidub.ui.screens.render_queue import RenderQueueScreen  # noqa: PLC0415
                    return RenderQueueScreen()

                if key == "export":
                    from aidub.ui.screens.export import ExportScreen  # noqa: PLC0415
                    return ExportScreen()

                if key == "models":
                    from aidub.ui.screens.misc_screens import ModelManagerScreen  # noqa: PLC0415
                    return ModelManagerScreen()

                if key == "providers":
                    from aidub.ui.screens.misc_screens import ProviderManagerScreen  # noqa: PLC0415
                    return ProviderManagerScreen()

                if key == "settings":
                    from aidub.ui.screens.misc_screens import SettingsScreen  # noqa: PLC0415
                    return SettingsScreen()

                if key == "wizard":
                    from aidub.ui.screens.project_wizard import ProjectWizardScreen  # noqa: PLC0415
                    s = ProjectWizardScreen()
                    s.project_created.connect(lambda _: self._navigate_to("analysis"))
                    s.cancelled.connect(lambda: self._navigate_to("dashboard"))
                    return s

            except Exception:
                logger.exception("Failed to load screen '%s'", key)

            return self._placeholder(key.title(), "Screen unavailable")

        @staticmethod
        def _placeholder(title: str, subtitle: str = "") -> QWidget:
            w = QWidget()
            w.setStyleSheet("background:#0D1118;")
            lay = QVBoxLayout(w)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t = QLabel(title, w)
            t.setObjectName("ScreenTitle")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(t)
            if subtitle:
                s = QLabel(subtitle, w)
                s.setObjectName("MutedLabel")
                s.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lay.addWidget(s)
            return w

        def navigate_to(self, key: str) -> None:
            """Public API: navigate to a named screen."""
            self._navigate_to(key)

        def closeEvent(self, event: QCloseEvent) -> None:
            """Background processing close prompt (Section 47.1)."""
            reply = QMessageBox.question(
                self,
                "Rendering & Background Jobs Running",
                "Rendering is currently in progress.\nDo you want to minimize to the System Tray to let rendering finish?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.ignore()
                self.hide()
                if hasattr(self, "_tray"):
                    self._tray.showMessage(
                        "AI Movie Dubbing Studio",
                        "Rendering continues in background system tray.",
                        QSystemTrayIcon.MessageIcon.Information,
                        3000,
                    )
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()


__all__ = ["AIDubStudioWindow"]
