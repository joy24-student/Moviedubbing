"""Phase-one desktop design tokens and Qt style sheet."""

from __future__ import annotations

APPLICATION_STYLE = """
QWidget {
    background: #11151b;
    color: #e8edf3;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 10pt;
}
QMainWindow::separator { background: #2b3440; width: 1px; height: 1px; }
QMenuBar, QMenu { background: #171c24; }
QMenuBar::item:selected, QMenu::item:selected { background: #283549; }
QFrame#PolicyBanner {
    background: #171e28;
    border-bottom: 1px solid #2b3440;
}
QLabel#BrandTitle { font-size: 15pt; font-weight: 650; color: #f5f7fa; }
QLabel#SectionTitle { font-size: 20pt; font-weight: 650; color: #f5f7fa; }
QLabel#SectionDescription { color: #aeb9c8; font-size: 10.5pt; }
QLabel#NavigationHeading { color: #8190a3; font-size: 8pt; font-weight: 700; }
QListWidget#Navigation {
    background: #151a21;
    border: 0;
    padding: 6px;
    outline: 0;
}
QListWidget#Navigation::item {
    border-radius: 5px;
    margin: 2px 0;
    padding: 10px 12px;
}
QListWidget#Navigation::item:selected { background: #254a77; color: #ffffff; }
QListWidget#Navigation::item:hover:!selected { background: #202934; }
QLabel[statusTone="safe"] {
    background: #123a2c; color: #a9efd0; border: 1px solid #216449;
    border-radius: 4px; padding: 5px 9px; font-weight: 600;
}
QLabel[statusTone="warning"] {
    background: #423416; color: #ffe39a; border: 1px solid #6f5724;
    border-radius: 4px; padding: 5px 9px; font-weight: 600;
}
QLabel[statusTone="danger"] {
    background: #442226; color: #ffc7ca; border: 1px solid #74373d;
    border-radius: 4px; padding: 5px 9px; font-weight: 600;
}
QLabel[statusTone="info"] {
    background: #1d3654; color: #c8e2ff; border: 1px solid #315d8b;
    border-radius: 4px; padding: 5px 9px; font-weight: 600;
}
QPushButton {
    background: #26313f; border: 1px solid #3c4a5c; border-radius: 5px;
    padding: 7px 14px;
}
QPushButton:hover { background: #304056; border-color: #50709a; }
QPushButton:focus { border: 2px solid #63a8ff; }
QPushButton[primary="true"] { background: #2468a9; border-color: #3987ce; }
QFrame#EmptyState, QFrame#StatusCard {
    background: #171d25; border: 1px solid #2b3542; border-radius: 6px;
}
QDockWidget { color: #dce4ed; font-weight: 600; }
QDockWidget::title { background: #1a2029; padding: 7px; }
QStatusBar { background: #171c24; color: #b4bfcc; }
QLineEdit, QComboBox {
    background: #202731; border: 1px solid #3a4655; border-radius: 4px; padding: 6px;
}
QLineEdit:focus, QComboBox:focus { border: 2px solid #63a8ff; }
QDialog#CommandPalette { background: #171d25; }
QListWidget#CommandResults { border: 0; background: #171d25; outline: 0; }
QListWidget#CommandResults::item { padding: 9px; border-bottom: 1px solid #29323e; }
QListWidget#CommandResults::item:selected { background: #254a77; }
"""
