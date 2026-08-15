"""Production-oriented Phase 0/1 native desktop shell."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .command_palette import CommandPaletteDialog
from .commands import Command, CommandRegistry
from .models import Connectivity, PrivacyMode, ShellState, ShellStatus
from .qt_support import PYSIDE6_AVAILABLE, DesktopDependencyError, desktop_dependency_message

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from aidub.i18n import LocaleService


if PYSIDE6_AVAILABLE:
    try:
        from PySide6.QtCore import Qt, Signal
        from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
        from PySide6.QtWidgets import (
            QComboBox,
            QDockWidget,
            QFrame,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QMenu,
            QSizePolicy,
            QStackedWidget,
            QStatusBar,
            QVBoxLayout,
            QWidget,
        )
    except Exception as _caught_qt_error:  # noqa: BLE001 - catches native Qt load errors.
        _QT_WIDGETS_AVAILABLE = False
        _QT_WIDGETS_IMPORT_ERROR: Exception | None = _caught_qt_error
    else:
        _QT_WIDGETS_AVAILABLE = True
        _QT_WIDGETS_IMPORT_ERROR = None
else:
    _QT_WIDGETS_AVAILABLE = False
    _QT_WIDGETS_IMPORT_ERROR = None


if _QT_WIDGETS_AVAILABLE:

    class _EmptyState(QFrame):  # type: ignore[misc]
        def __init__(
            self,
            text_key: str,
            locale: LocaleService,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self.setObjectName("EmptyState")
            self._text_key = text_key
            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 18, 20, 18)
            self.label = QLabel(self)
            self.label.setWordWrap(True)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.label)
            self.refresh_texts(locale)

        def refresh_texts(self, locale: LocaleService) -> None:
            self.label.setText(locale(self._text_key))

    class _TextPage(QWidget):  # type: ignore[misc]
        def __init__(
            self,
            title_key: str,
            description_key: str,
            empty_key: str,
            locale: LocaleService,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self._title_key = title_key
            self._description_key = description_key
            layout = QVBoxLayout(self)
            layout.setContentsMargins(34, 30, 34, 30)
            layout.setSpacing(12)
            self.title_label = QLabel(self)
            self.title_label.setObjectName("SectionTitle")
            self.description_label = QLabel(self)
            self.description_label.setObjectName("SectionDescription")
            self.description_label.setWordWrap(True)
            self.empty_state = _EmptyState(empty_key, locale, self)
            layout.addWidget(self.title_label)
            layout.addWidget(self.description_label)
            layout.addSpacing(14)
            layout.addWidget(self.empty_state)
            layout.addStretch(1)
            _TextPage.refresh_texts(self, locale)

        def refresh_texts(self, locale: LocaleService) -> None:
            self.title_label.setText(locale(self._title_key))
            self.description_label.setText(locale(self._description_key))
            self.empty_state.refresh_texts(locale)

    class _HomePage(_TextPage):
        def __init__(self, locale: LocaleService, parent: QWidget | None = None) -> None:
            super().__init__("home.title", "home.description", "home.empty", locale, parent)
            self._recent_label = QLabel(self)
            self._recent_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
            layout = self.layout()
            layout.insertWidget(2, self._recent_label)
            self.refresh_texts(locale)

        def refresh_texts(self, locale: LocaleService) -> None:
            super().refresh_texts(locale)
            self._recent_label.setText(locale("home.recent_projects"))

    class _StatusCard(QFrame):  # type: ignore[misc]
        def __init__(self, title_key: str, value_key: str, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("StatusCard")
            self.title_key = title_key
            self.value_key = value_key
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 13, 16, 13)
            self.title_label = QLabel(self)
            self.title_label.setStyleSheet("font-weight: 650;")
            self.value_label = QLabel(self)
            self.value_label.setObjectName("SectionDescription")
            self.value_label.setWordWrap(True)
            layout.addWidget(self.title_label)
            layout.addWidget(self.value_label)

        def refresh_texts(self, locale: LocaleService) -> None:
            self.title_label.setText(locale(self.title_key))
            self.value_label.setText(locale(self.value_key))

    class _SystemPage(QWidget):  # type: ignore[misc]
        def __init__(self, locale: LocaleService, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self._status = ShellStatus()
            layout = QVBoxLayout(self)
            layout.setContentsMargins(34, 30, 34, 30)
            layout.setSpacing(12)
            self.title_label = QLabel(self)
            self.title_label.setObjectName("SectionTitle")
            self.description_label = QLabel(self)
            self.description_label.setObjectName("SectionDescription")
            self.description_label.setWordWrap(True)
            layout.addWidget(self.title_label)
            layout.addWidget(self.description_label)
            layout.addSpacing(12)
            self.cards = (
                _StatusCard("system.local_engine", "system.local_engine_value", self),
                _StatusCard("system.providers", "system.providers_value", self),
                _StatusCard("system.storage", "system.storage_value", self),
                _StatusCard("system.gpu", "system.gpu_value", self),
            )
            for card in self.cards:
                layout.addWidget(card)
            layout.addStretch(1)
            self.refresh_texts(locale)

        def set_status(self, status: ShellStatus, locale: LocaleService) -> None:
            self._status = status
            provider_keys = {
                Connectivity.OFFLINE: "system.providers_value",
                Connectivity.ONLINE: "system.providers_value_online",
                Connectivity.DEGRADED: "system.providers_value_degraded",
            }
            self.cards[1].value_key = provider_keys[status.connectivity]
            self.refresh_texts(locale)

        def refresh_texts(self, locale: LocaleService) -> None:
            self.title_label.setText(locale("system.title"))
            self.description_label.setText(locale("system.description"))
            for card in self.cards:
                card.refresh_texts(locale)

    class _PolicyBanner(QFrame):  # type: ignore[misc]
        def __init__(self, locale: LocaleService, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("PolicyBanner")
            self._locale = locale
            self._status = ShellStatus()
            layout = QHBoxLayout(self)
            layout.setContentsMargins(12, 7, 12, 7)
            layout.setSpacing(8)
            self.connectivity_label = QLabel(self)
            self.privacy_label = QLabel(self)
            self.language_label = QLabel(self)
            self.locale_combo = QComboBox(self)
            self.locale_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            layout.addWidget(self.connectivity_label)
            layout.addWidget(self.privacy_label)
            layout.addStretch(1)
            layout.addWidget(self.language_label)
            layout.addWidget(self.locale_combo)
            self.refresh_catalogs()
            self.apply_status(self._status)

        def refresh_catalogs(self) -> None:
            self.locale_combo.blockSignals(True)  # noqa: FBT003 - Qt positional API.
            self.locale_combo.clear()
            selected = 0
            for index, catalog in enumerate(self._locale.catalogs()):
                self.locale_combo.addItem(catalog.native_name, catalog.locale)
                if catalog.locale == self._locale.locale:
                    selected = index
            self.locale_combo.setCurrentIndex(selected)
            self.locale_combo.blockSignals(False)  # noqa: FBT003 - Qt positional API.

        @staticmethod
        def _repolish(widget: QWidget) -> None:
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        def apply_status(self, status: ShellStatus) -> None:
            self._status = status
            connectivity_keys = {
                Connectivity.OFFLINE: ("status.offline", "status.offline_detail", "safe"),
                Connectivity.ONLINE: ("status.online", "status.online_detail", "info"),
                Connectivity.DEGRADED: ("status.degraded", "status.degraded_detail", "warning"),
            }
            privacy_keys = {
                PrivacyMode.LOCAL_ONLY: ("privacy.local_only", "privacy.local_only_detail", "safe"),
                PrivacyMode.HYBRID: ("privacy.hybrid", "privacy.hybrid_detail", "warning"),
                PrivacyMode.CLOUD_ALLOWED: (
                    "privacy.cloud_allowed",
                    "privacy.cloud_allowed_detail",
                    "danger",
                ),
            }
            connectivity_key, connectivity_detail, connectivity_tone = connectivity_keys[
                status.connectivity
            ]
            privacy_key, privacy_detail, privacy_tone = privacy_keys[status.privacy_mode]
            connectivity_text = self._locale(connectivity_key)
            privacy_text = self._locale(privacy_key)
            self.connectivity_label.setText(
                f"{self._locale('status.connectivity')}: {connectivity_text}"
            )
            self.connectivity_label.setToolTip(self._locale(connectivity_detail))
            accessible_connectivity = (
                self._locale("accessibility.offline")
                if status.connectivity is Connectivity.OFFLINE
                else connectivity_text
            )
            self.connectivity_label.setAccessibleName(accessible_connectivity)
            self.connectivity_label.setProperty("statusTone", connectivity_tone)
            self.privacy_label.setText(f"{self._locale('status.privacy')}: {privacy_text}")
            self.privacy_label.setToolTip(self._locale(privacy_detail))
            self.privacy_label.setAccessibleName(
                self._locale("accessibility.privacy", mode=privacy_text)
            )
            self.privacy_label.setProperty("statusTone", privacy_tone)
            self._repolish(self.connectivity_label)
            self._repolish(self.privacy_label)

        def refresh_texts(self) -> None:
            self.language_label.setText(self._locale("language.label"))
            self.locale_combo.setAccessibleName(self._locale("language.label"))
            self.refresh_catalogs()
            self.apply_status(self._status)

    class AIDubMainWindow(QMainWindow):  # type: ignore[misc]
        """Dock-capable shell for all current and future editor workspaces."""

        locale_changed = Signal(str)
        shell_status_changed = Signal(object)

        NAVIGATION = (
            ("workspace.home", "nav.home"),
            ("workspace.projects", "nav.projects"),
            ("workspace.jobs", "nav.jobs"),
            ("workspace.system", "nav.system"),
        )

        def __init__(
            self,
            locale_service: LocaleService,
            *,
            shell_state: ShellState | None = None,
            command_registry: CommandRegistry | None = None,
            parent: QWidget | None = None,
        ) -> None:
            super().__init__(parent)
            self.locale_service = locale_service
            self.shell_state = shell_state or ShellState()
            self.command_registry = command_registry or CommandRegistry()
            self._actions: dict[str, QAction] = {}
            self._menus: dict[str, QMenu] = {}
            self._docks: dict[str, tuple[QDockWidget, str]] = {}
            self._navigation_sync = False
            self._closed = False

            self.setObjectName("AIDubMainWindow")
            self.setDockNestingEnabled(True)
            self.setAnimated(False)
            self.resize(1280, 800)
            self.setMinimumSize(900, 600)
            self._build_central_workspace()
            self._build_default_docks()
            self._register_shell_commands()
            self._build_menus()
            self._build_status_bar()

            self.locale_changed.connect(self._apply_locale)
            self.shell_status_changed.connect(self._apply_status)
            self._unsubscribe_locale = self.locale_service.subscribe(self.locale_changed.emit)
            self._unsubscribe_status = self.shell_state.subscribe(self.shell_status_changed.emit)
            self._policy_banner.locale_combo.currentIndexChanged.connect(self._select_locale)
            self._navigation.currentRowChanged.connect(self._activate_navigation_row)
            self._navigate(0)
            self._apply_locale(self.locale_service.locale)
            self._apply_status(self.shell_state.status)

        @property
        def docks(self) -> tuple[str, ...]:
            return tuple(self._docks)

        def register_dock(
            self,
            dock_id: str,
            title_key: str,
            widget: QWidget,
            *,
            area: Qt.DockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea,
            allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas,
        ) -> QDockWidget:
            if not dock_id or dock_id in self._docks:
                raise ValueError(f"Dock id must be non-empty and unique: '{dock_id}'.")
            dock = QDockWidget(self)
            dock.setObjectName(f"dock.{dock_id}")
            dock.setAllowedAreas(allowed_areas)
            dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable
                | QDockWidget.DockWidgetFeature.DockWidgetFloatable
                | QDockWidget.DockWidgetFeature.DockWidgetClosable
            )
            dock.setWidget(widget)
            self.addDockWidget(area, dock)
            self._docks[dock_id] = (dock, title_key)
            dock.setWindowTitle(self.locale_service(title_key))
            return dock

        def unregister_dock(self, dock_id: str) -> QWidget:
            try:
                dock, _title_key = self._docks.pop(dock_id)
            except KeyError as exc:
                raise KeyError(f"Unknown dock '{dock_id}'.") from exc
            widget = dock.widget()
            dock.setWidget(None)
            self.removeDockWidget(dock)
            dock.deleteLater()
            return widget

        def _build_central_workspace(self) -> None:
            central = QWidget(self)
            outer = QVBoxLayout(central)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)
            self._policy_banner = _PolicyBanner(self.locale_service, central)
            outer.addWidget(self._policy_banner)

            body = QWidget(central)
            body_layout = QHBoxLayout(body)
            body_layout.setContentsMargins(0, 0, 0, 0)
            body_layout.setSpacing(0)
            sidebar = QFrame(body)
            sidebar.setFixedWidth(220)
            sidebar.setStyleSheet("background: #151a21; border-right: 1px solid #2b3440;")
            sidebar_layout = QVBoxLayout(sidebar)
            sidebar_layout.setContentsMargins(12, 16, 12, 12)
            self._brand_label = QLabel(sidebar)
            self._brand_label.setObjectName("BrandTitle")
            self._brand_label.setWordWrap(True)
            self._nav_heading = QLabel(sidebar)
            self._nav_heading.setObjectName("NavigationHeading")
            self._navigation = QListWidget(sidebar)
            self._navigation.setObjectName("Navigation")
            for command_id, label_key in self.NAVIGATION:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, command_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, label_key)
                self._navigation.addItem(item)
            sidebar_layout.addWidget(self._brand_label)
            sidebar_layout.addSpacing(22)
            sidebar_layout.addWidget(self._nav_heading)
            sidebar_layout.addWidget(self._navigation, 1)

            self._stack = QStackedWidget(body)
            self._pages: tuple[QWidget, ...] = (
                _HomePage(self.locale_service, self._stack),
                _TextPage(
                    "projects.title",
                    "projects.description",
                    "projects.empty",
                    self.locale_service,
                    self._stack,
                ),
                _TextPage(
                    "jobs.title",
                    "jobs.description",
                    "jobs.empty",
                    self.locale_service,
                    self._stack,
                ),
                _SystemPage(self.locale_service, self._stack),
            )
            for page in self._pages:
                self._stack.addWidget(page)
            body_layout.addWidget(sidebar)
            body_layout.addWidget(self._stack, 1)
            outer.addWidget(body, 1)
            self.setCentralWidget(central)

        def _placeholder_widget(self, label_key: str) -> QWidget:
            container = QWidget(self)
            layout = QVBoxLayout(container)
            label = QLabel(container)
            label.setProperty("translationKey", label_key)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(label)
            layout.addStretch(1)
            return container

        def _build_default_docks(self) -> None:
            self.register_dock(
                "activity",
                "dock.activity",
                self._placeholder_widget("dock.activity.empty"),
                area=Qt.DockWidgetArea.BottomDockWidgetArea,
            )
            self.register_dock(
                "inspector",
                "dock.inspector",
                self._placeholder_widget("dock.inspector.empty"),
                area=Qt.DockWidgetArea.RightDockWidgetArea,
            )
            self._docks["activity"][0].hide()

        def _register_shell_commands(self) -> None:
            commands = [
                Command(
                    "workspace.home",
                    "command.home",
                    lambda: self._navigate(0),
                    shortcuts=("Alt+1",),
                    category="workspace",
                    order=10,
                ),
                Command(
                    "workspace.projects",
                    "command.projects",
                    lambda: self._navigate(1),
                    shortcuts=("Alt+2",),
                    category="workspace",
                    order=20,
                ),
                Command(
                    "workspace.jobs",
                    "command.jobs",
                    lambda: self._navigate(2),
                    shortcuts=("Alt+3",),
                    category="workspace",
                    order=30,
                ),
                Command(
                    "workspace.system",
                    "command.system",
                    lambda: self._navigate(3),
                    shortcuts=("Alt+4",),
                    category="workspace",
                    order=40,
                ),
                Command(
                    "view.command_palette",
                    "command.palette",
                    self._open_command_palette,
                    shortcuts=("Ctrl+K",),
                    category="view",
                    order=10,
                ),
                Command(
                    "view.toggle_activity",
                    "command.toggle_activity",
                    lambda: self._toggle_dock("activity"),
                    category="view",
                    order=20,
                ),
                Command(
                    "view.toggle_inspector",
                    "command.toggle_inspector",
                    lambda: self._toggle_dock("inspector"),
                    category="view",
                    order=30,
                ),
                Command(
                    "app.quit",
                    "command.quit",
                    self.close,
                    shortcuts=("Ctrl+Q",),
                    category="application",
                    order=1000,
                ),
            ]
            self.command_registry.register_many(
                command for command in commands if command.command_id not in self.command_registry
            )
            for command in commands:
                self._actions[command.command_id] = self._create_action(command.command_id)

        def _create_action(self, command_id: str) -> QAction:
            command = self.command_registry.get(command_id)
            action = QAction(self)
            action.setObjectName(f"action.{command_id}")
            if command.shortcuts:
                action.setShortcuts([QKeySequence(shortcut) for shortcut in command.shortcuts])
            action.triggered.connect(
                lambda _checked=False, identifier=command_id: self.command_registry.execute(
                    identifier
                )
            )
            action.setEnabled(command.is_enabled())
            self.addAction(action)
            return action

        def _build_menus(self) -> None:
            menu_bar = self.menuBar()
            self._menus["file"] = menu_bar.addMenu("")
            self._menus["workspace"] = menu_bar.addMenu("")
            self._menus["view"] = menu_bar.addMenu("")
            self._menus["language"] = menu_bar.addMenu("")
            self._menus["file"].addAction(self._actions["app.quit"])
            for command_id, _label in self.NAVIGATION:
                self._menus["workspace"].addAction(self._actions[command_id])
            self._menus["view"].addAction(self._actions["view.command_palette"])
            self._menus["view"].addSeparator()
            self._menus["view"].addAction(self._actions["view.toggle_activity"])
            self._menus["view"].addAction(self._actions["view.toggle_inspector"])
            self._language_group = QActionGroup(self)
            self._language_group.setExclusive(True)
            for catalog in self.locale_service.catalogs():
                action = QAction(catalog.native_name, self)
                action.setCheckable(True)
                action.setData(catalog.locale)
                action.setChecked(catalog.locale == self.locale_service.locale)
                action.triggered.connect(
                    lambda _checked=False, locale_name=catalog.locale: (
                        self.locale_service.set_locale(locale_name)
                    )
                )
                self._language_group.addAction(action)
                self._menus["language"].addAction(action)

        def _build_status_bar(self) -> None:
            status = QStatusBar(self)
            self.setStatusBar(status)
            self._ready_label = QLabel(status)
            self._project_label = QLabel(status)
            self._project_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            status.addWidget(self._project_label, 1)
            status.addPermanentWidget(self._ready_label)

        def _toggle_dock(self, dock_id: str) -> None:
            dock = self._docks[dock_id][0]
            dock.setVisible(not dock.isVisible())

        def _open_command_palette(self) -> None:
            CommandPaletteDialog(self.command_registry, self.locale_service, self).exec()

        def _navigate(self, index: int) -> None:
            if not 0 <= index < len(self._pages):
                raise IndexError(f"Unknown workspace page index {index}.")
            self._navigation_sync = True
            self._navigation.setCurrentRow(index)
            self._stack.setCurrentIndex(index)
            self._navigation_sync = False

        def _activate_navigation_row(self, row: int) -> None:
            if self._navigation_sync or row < 0:
                return
            item = self._navigation.item(row)
            self.command_registry.execute(str(item.data(Qt.ItemDataRole.UserRole)))

        def _select_locale(self, index: int) -> None:
            locale_name = self._policy_banner.locale_combo.itemData(index)
            if locale_name:
                self.locale_service.set_locale(str(locale_name))

        def _apply_locale(self, _locale_name: str) -> None:
            self.setWindowTitle(self.locale_service("app.title"))
            direction = (
                Qt.LayoutDirection.RightToLeft
                if self.locale_service.direction == "rtl"
                else Qt.LayoutDirection.LeftToRight
            )
            self.centralWidget().setLayoutDirection(direction)
            self._brand_label.setText(self.locale_service("app.title"))
            self._brand_label.setToolTip(self.locale_service("app.subtitle"))
            self._nav_heading.setText(self.locale_service("nav.workspace"))
            for index in range(self._navigation.count()):
                item = self._navigation.item(index)
                item.setText(self.locale_service(str(item.data(Qt.ItemDataRole.UserRole + 1))))
            for page in self._pages:
                refresh = getattr(page, "refresh_texts", None)
                if callable(refresh):
                    refresh(self.locale_service)
            for dock, title_key in self._docks.values():
                dock.setWindowTitle(self.locale_service(title_key))
                label = dock.widget().findChild(QLabel)
                if label is not None:
                    label.setText(self.locale_service(str(label.property("translationKey"))))
            menu_keys = {
                "file": "menu.file",
                "workspace": "menu.workspace",
                "view": "menu.view",
                "language": "menu.language",
            }
            for menu_id, title_key in menu_keys.items():
                self._menus[menu_id].setTitle(self.locale_service(title_key))
            for command_id, action in self._actions.items():
                action.setText(self.locale_service(self.command_registry.get(command_id).title_key))
            for action in self._language_group.actions():
                action.setChecked(action.data() == self.locale_service.locale)
            self._policy_banner.refresh_texts()
            self._apply_status(self.shell_state.status)

        def _apply_status(self, status: ShellStatus) -> None:
            self._policy_banner.apply_status(status)
            system_page = self._pages[3]
            if isinstance(system_page, _SystemPage):
                system_page.set_status(status, self.locale_service)
            ready_key = "status.ready" if status.ready else "status.degraded"
            self._ready_label.setText(self.locale_service(ready_key))
            self._project_label.setText(
                status.active_project_name or self.locale_service("status.no_active_project")
            )

        @override
        def closeEvent(self, event: QCloseEvent) -> None:
            if not self._closed:
                self._closed = True
                self._unsubscribe_locale()
                self._unsubscribe_status()
            super().closeEvent(event)

else:

    class AIDubMainWindow:  # type: ignore[no-redef]  # pragma: no cover
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            detail = (
                f"\nQt Widgets error: {_QT_WIDGETS_IMPORT_ERROR}"
                if _QT_WIDGETS_IMPORT_ERROR
                else ""
            )
            raise DesktopDependencyError(desktop_dependency_message() + detail)
