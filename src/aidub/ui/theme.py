"""
Broadcast-grade enterprise theme design tokens and Qt style generator.

Color system inspired by Hollywood NLE standards (DaVinci Resolve / Premiere Pro):
  - Primary Background: #121216 (Deep Slate)
  - Surface Card: #1E1E24 (Dark Charcoal)
  - Panel Border: #2D2D38
  - Primary Accent: #6366F1 (Studio Indigo)
  - Success / Active: #10B981 (Emerald)
  - Warning / Alert: #F59E0B (Amber)
  - Danger / Lock: #EF4444 (Crimson)
  - Text Primary: #F9FAFB
  - Text Muted: #9CA3AF
"""

from __future__ import annotations

from enum import StrEnum

from aidub.contracts.base import ContractModel


class ThemeMode(StrEnum):
    STUDIO_DARK = "studio_dark"
    BROADCAST_GRAY = "broadcast_gray"
    HIGH_CONTRAST = "high_contrast"


class ColorTokens(ContractModel):
    bg_dark: str = "#121216"
    bg_surface: str = "#1E1E24"
    bg_elevated: str = "#2A2A34"
    border: str = "#2D2D38"
    accent: str = "#6366F1"
    accent_hover: str = "#4F46E5"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    text_primary: str = "#F9FAFB"
    text_secondary: str = "#D1D5DB"
    text_muted: str = "#9CA3AF"


TRACK_COLOR_PALETTE: dict[str, str] = {
    "V1": "#3B82F6",  # Blue
    "V2": "#8B5CF6",  # Purple
    "A1": "#10B981",  # Emerald
    "A2": "#6366F1",  # Indigo
    "A3": "#F59E0B",  # Amber
    "A4": "#EC4899",  # Pink
    "A5": "#14B8A6",  # Teal
    "S1": "#F97316",  # Orange
    "S2": "#06B6D4",  # Cyan
}


def build_enterprise_stylesheet(tokens: ColorTokens | None = None) -> str:
    """Generate comprehensive QSS stylesheet for the application."""
    t = tokens or ColorTokens()
    return f"""
    QWidget {{
        background-color: {t.bg_dark};
        color: {t.text_primary};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 10pt;
    }}
    QMainWindow::separator {{
        background-color: {t.border};
        width: 2px;
        height: 2px;
    }}
    QFrame.StudioCard {{
        background-color: {t.bg_surface};
        border: 1px solid {t.border};
        border-radius: 8px;
    }}
    QPushButton {{
        background-color: {t.bg_elevated};
        color: {t.text_primary};
        border: 1px solid {t.border};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {t.accent_hover};
        border-color: {t.accent};
    }}
    QPushButton.Primary {{
        background-color: {t.accent};
        color: #FFFFFF;
    }}
    QLineEdit, QTextEdit, QSpinBox {{
        background-color: {t.bg_surface};
        color: {t.text_primary};
        border: 1px solid {t.border};
        border-radius: 4px;
        padding: 6px 10px;
    }}
    QLineEdit:focus {{
        border-color: {t.accent};
    }}
    QListWidget, QTreeWidget {{
        background-color: {t.bg_surface};
        border: 1px solid {t.border};
        border-radius: 6px;
    }}
    QListWidget::item:selected {{
        background-color: {t.accent};
        color: #FFFFFF;
        border-radius: 4px;
    }}
    """


__all__ = [
    "TRACK_COLOR_PALETTE",
    "ColorTokens",
    "ThemeMode",
    "build_enterprise_stylesheet",
]
