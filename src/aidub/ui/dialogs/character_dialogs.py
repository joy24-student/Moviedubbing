"""
Character Speaker Merge, Split, and Assign dialogs (Master Spec Section 14.4 & 19).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


if _QT:

    class MergeSpeakerDialog(QDialog):  # type: ignore[misc]
        """Merge two detected speaker profiles into a single character."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("Merge Speaker Profiles")
            self.setFixedSize(440, 240)
            self.setModal(True)
            self.setStyleSheet("QDialog{background:#161D28;} QLabel{color:#F7F9FC;}")

            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(12)

            layout.addWidget(QLabel("Select Primary Speaker Profile:", self))
            self.primary_cb = QComboBox(self)
            self.primary_cb.addItems(["Tony Stark (SPK_003)", "Pepper Potts (SPK_001)", "Unknown 01 (SPK_008)"])
            layout.addWidget(self.primary_cb)

            layout.addWidget(QLabel("Select Speaker Profile to Merge Into Primary:", self))
            self.secondary_cb = QComboBox(self)
            self.secondary_cb.addItems(["Unknown 01 (SPK_008)", "Unknown 02 (SPK_009)", "SPK_012"])
            layout.addWidget(self.secondary_cb)

            btns = QHBoxLayout()
            btns.setSpacing(10)
            cancel = QPushButton("Cancel", self)
            cancel.clicked.connect(self.reject)
            btns.addWidget(cancel)

            merge_btn = QPushButton("Merge Speakers", self)
            merge_btn.setProperty("primary", "true")
            merge_btn.clicked.connect(self.accept)
            btns.addWidget(merge_btn)

            layout.addLayout(btns)

    class SplitSpeakerDialog(QDialog):  # type: ignore[misc]
        """Split a speaker profile at a given timecode point."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("Split Speaker Profile")
            self.setFixedSize(440, 220)
            self.setModal(True)
            self.setStyleSheet("QDialog{background:#161D28;} QLabel{color:#F7F9FC;}")

            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(12)

            layout.addWidget(QLabel("Speaker Profile to Split:", self))
            self.spk_cb = QComboBox(self)
            self.spk_cb.addItems(["Tony Stark (SPK_003)", "Pepper Potts (SPK_001)", "Unknown 01 (SPK_008)"])
            layout.addWidget(self.spk_cb)

            layout.addWidget(QLabel("Split Timecode (HH:MM:SS.mmm):", self))
            self.tc_edit = QLineEdit("00:22:14.500", self)
            layout.addWidget(self.tc_edit)

            btns = QHBoxLayout()
            btns.setSpacing(10)
            cancel = QPushButton("Cancel", self)
            cancel.clicked.connect(self.reject)
            btns.addWidget(cancel)

            split_btn = QPushButton("Split Speaker", self)
            split_btn.setProperty("primary", "true")
            split_btn.clicked.connect(self.accept)
            btns.addWidget(split_btn)

            layout.addLayout(btns)

    class AssignVoiceDialog(QDialog):  # type: ignore[misc]
        """Assign reference voice audio file to character."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("Assign Voice Profile")
            self.setFixedSize(480, 220)
            self.setModal(True)
            self.setStyleSheet("QDialog{background:#161D28;} QLabel{color:#F7F9FC;}")

            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(12)

            layout.addWidget(QLabel("Select Reference Audio File (.wav, .mp3, .flac):", self))
            row = QHBoxLayout()
            self.path_edit = QLineEdit("D:\\Voices\\Tony_Ref.wav", self)
            row.addWidget(self.path_edit)
            browse = QPushButton("Browse…", self)
            browse.clicked.connect(self._browse)
            row.addWidget(browse)
            layout.addLayout(row)

            btns = QHBoxLayout()
            btns.setSpacing(10)
            cancel = QPushButton("Cancel", self)
            cancel.clicked.connect(self.reject)
            btns.addWidget(cancel)

            assign_btn = QPushButton("Assign Voice", self)
            assign_btn.setProperty("primary", "true")
            assign_btn.clicked.connect(self.accept)
            btns.addWidget(assign_btn)

            layout.addLayout(btns)

        def _browse(self) -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Select Voice File", "", "Audio Files (*.wav *.mp3 *.flac)")
            if path:
                self.path_edit.setText(path)


__all__ = [
    "AssignVoiceDialog",
    "MergeSpeakerDialog",
    "SplitSpeakerDialog",
]
