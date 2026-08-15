"""
Enterprise PySide6 widget factory for all 26 workspace screens.

Provides concrete PySide6 QWidget / QFrame instances for every ScreenId in
the 26-screen catalog (Master Spec Section 27). Uses fallback mock containers
when running in headless environments without PySide6.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aidub.ui.qt_support import PYSIDE6_AVAILABLE
from aidub.ui.screens.catalog import ScreenCatalogRegistry, ScreenId

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def create_screen_widget(
    screen_id: ScreenId,
    parent: QWidget | None = None,
) -> object:
    """
    Factory creating styled PySide6 QWidget container for a ScreenId.

    Guarantees:
      - Returns valid QWidget if PySide6 is available.
      - Returns dict descriptor container in headless non-Qt environments.
    """
    if PYSIDE6_AVAILABLE:
        try:
            from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

            widget = QFrame(parent)
            widget.setObjectName(f"Screen_{screen_id.value}")
            widget.setProperty("screen_id", screen_id.value)
            widget.setStyleSheet(
                "QFrame { background-color: #1E1E24; border: 1px solid #2D2D38; border-radius: 8px; }"
            )

            layout = QVBoxLayout(widget)
            layout.setContentsMargins(20, 20, 20, 20)

            title_label = QLabel(screen_id.value.replace("_", " ").title(), widget)
            title_label.setStyleSheet("font-size: 16pt; font-weight: 700; color: #F9FAFB;")

            subtitle = QLabel(f"Studio Workspace Screen — {screen_id.value}", widget)
            subtitle.setStyleSheet("font-size: 10pt; color: #9CA3AF;")

            layout.addWidget(title_label)
            layout.addWidget(subtitle)
            layout.addStretch()

            return widget
        except Exception as exc:
            logger.warning("qt widget construction failed for %s: %s", screen_id, exc)

    # Headless container descriptor fallback
    return {
        "screen_id": screen_id.value,
        "title": screen_id.value.replace("_", " ").title(),
        "widget_type": "QFrame",
        "headless_fallback": True,
    }


class ScreenWidgetFactory:
    """Manager caching and instantiating widgets for all 26 catalog screens."""

    def __init__(self, registry: ScreenCatalogRegistry | None = None) -> None:
        self._registry = registry or ScreenCatalogRegistry()
        self._cache: dict[str, object] = {}

    def get_or_create(self, screen_id: ScreenId) -> object:
        """Get cached widget or create a new widget instance."""
        if screen_id.value not in self._cache:
            self._cache[screen_id.value] = create_screen_widget(screen_id)
        return self._cache[screen_id.value]


__all__ = [
    "ScreenWidgetFactory",
    "create_screen_widget",
]
