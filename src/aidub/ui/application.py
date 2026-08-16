"""Desktop application lifecycle and a graceful optional-dependency entrypoint."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from aidub import __version__
from aidub.i18n import CatalogError, LocaleService

from .models import ShellState
from .qt_support import DesktopDependencyError, require_pyside6
from .styles import APPLICATION_STYLE

if TYPE_CHECKING:
    from collections.abc import Sequence


class DesktopApplication:
    """Own the Qt application, localization service and top-level window."""

    def __init__(
        self,
        argv: Sequence[str] | None = None,
        *,
        locale: str | None = None,
        shell_state: ShellState | None = None,
    ) -> None:
        require_pyside6()
        from PySide6.QtCore import QCoreApplication  # noqa: PLC0415
        from PySide6.QtWidgets import QApplication  # noqa: PLC0415

        from .main_window import AIDubMainWindow  # noqa: PLC0415

        existing = QApplication.instance()
        self.application = existing or QApplication(list(argv) if argv is not None else sys.argv)
        self.owns_application = existing is None
        QCoreApplication.setOrganizationName("AI Dubbing Studio")
        QCoreApplication.setOrganizationDomain("aidubbing.studio")
        QCoreApplication.setApplicationName("AI Movie Dubbing Studio")
        QCoreApplication.setApplicationVersion(__version__)
        self.application.setStyleSheet(APPLICATION_STYLE)
        self.locale_service = LocaleService(locale)
        self.shell_state = shell_state or ShellState()
        self.window = AIDubMainWindow(self.locale_service, shell_state=self.shell_state)

    def show(self) -> None:
        self.window.show()

    def run(self) -> int:
        self.show()
        return int(self.application.exec())


def run_desktop(argv: Sequence[str] | None = None, *, locale: str | None = None) -> int:
    """Start the desktop UI and return a process exit code.

    Missing Qt packages and damaged localization resources are reported as
    concise operator diagnostics, making this safe as a console-script target.
    """

    try:
        desktop = DesktopApplication(argv, locale=locale)
    except (DesktopDependencyError, CatalogError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    return desktop.run()


if __name__ == "__main__":
    sys.exit(run_desktop())

