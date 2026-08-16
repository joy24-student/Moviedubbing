"""
AI Movie Dubbing Studio — Desktop launcher.

Usage:
    python launch_studio.py
    python -m aidub.ui.launch_studio
"""

from __future__ import annotations

import sys
import logging

logging.basicConfig(level=logging.WARNING)


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
    except ImportError:
        print("PySide6 not installed. Run: pip install PySide6>=6.9")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("AI Movie Dubbing Studio")
    app.setOrganizationName("SkillBridge")
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Apply base style before window creates
    from aidub.ui.styles import APPLICATION_STYLE  # noqa: PLC0415
    app.setStyleSheet(APPLICATION_STYLE)

    from aidub.ui.studio_window import AIDubStudioWindow  # noqa: PLC0415
    window = AIDubStudioWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
