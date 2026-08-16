"""
Crash Recovery & Missing Media Relink dialogs (Master Spec Section 60 & 61).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
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

    class CrashRecoveryDialog(QDialog):  # type: ignore[misc]
        """
        Autonomous crash recovery prompt dialog.
        Displays last operation state and journal snapshot point.
        """

        RECOVER = 1
        READ_ONLY = 2
        DISCARD = 3

        def __init__(
            self,
            project_name: str = "Avengers Bengali Dub",
            last_autosave: str = "00:31:24",
            last_operation: str = "Voice Generation — Scene 84",
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.result_action = self.RECOVER
            self.setWindowTitle("Crash Recovery Available")
            self.setFixedSize(500, 320)
            self.setModal(True)
            self.setStyleSheet(
                "QDialog{background:#161D28;border:1px solid #34415A;border-radius:12px;}"
                "QLabel{color:#F7F9FC;}"
            )

            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 20, 24, 20)
            layout.setSpacing(16)

            # Header
            hdr = QHBoxLayout()
            warn_icon = QLabel("⚠️", self)
            warn_icon.setStyleSheet("font-size:36px;")
            hdr.addWidget(warn_icon)

            title_box = QVBoxLayout()
            title = QLabel("RECOVERY AVAILABLE", self)
            title.setStyleSheet("font-size:18px;font-weight:700;color:#F59E0B;")
            title_box.addWidget(title)
            sub = QLabel("The application was closed unexpectedly during the previous session.", self)
            sub.setStyleSheet("font-size:12px;color:#A9B2C3;")
            title_box.addWidget(sub)
            hdr.addLayout(title_box)
            layout.addLayout(hdr)

            # Details card
            card = QFrame(self)
            card.setStyleSheet("QFrame{background:#0D1118;border:1px solid #283241;border-radius:8px;padding:12px;}")
            c_lay = QGridLayout(card)
            c_lay.setSpacing(8)

            fields = [
                ("Project Name", project_name),
                ("Last Autosave", last_autosave),
                ("Last Completed Stage", last_operation),
                ("Journal Status", "Valid • 100% Intact"),
            ]
            for i, (k, v) in enumerate(fields):
                kl = QLabel(f"{k}:", card)
                kl.setStyleSheet("font-size:12px;color:#687386;")
                vl = QLabel(v, card)
                vl.setStyleSheet("font-size:13px;font-weight:600;color:#F7F9FC;")
                c_lay.addWidget(kl, i, 0)
                c_lay.addWidget(vl, i, 1)

            layout.addWidget(card)

            # Action buttons
            btns = QHBoxLayout()
            btns.setSpacing(10)

            discard_btn = QPushButton("Discard Recovery", self)
            discard_btn.setFixedHeight(38)
            discard_btn.setProperty("accent", "danger")
            discard_btn.clicked.connect(self._on_discard)
            btns.addWidget(discard_btn)

            ro_btn = QPushButton("Open Read Only", self)
            ro_btn.setFixedHeight(38)
            ro_btn.clicked.connect(self._on_read_only)
            btns.addWidget(ro_btn)

            rec_btn = QPushButton("Recover Project", self)
            rec_btn.setFixedHeight(38)
            rec_btn.setProperty("primary", "true")
            rec_btn.clicked.connect(self._on_recover)
            btns.addWidget(rec_btn)

            layout.addLayout(btns)

        def _on_recover(self) -> None:
            self.result_action = self.RECOVER
            self.accept()

        def _on_read_only(self) -> None:
            self.result_action = self.READ_ONLY
            self.accept()

        def _on_discard(self) -> None:
            self.result_action = self.DISCARD
            self.reject()

    class MissingFileRelinkDialog(QDialog):  # type: ignore[misc]
        """
        Missing media source relink dialog.
        """

        def __init__(
            self,
            missing_file_path: str = "D:\\Movies\\movie.mkv",
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.relinquished_path = ""
            self.setWindowTitle("Missing Media Source File")
            self.setFixedSize(520, 260)
            self.setModal(True)
            self.setStyleSheet(
                "QDialog{background:#161D28;border:1px solid #34415A;border-radius:12px;}"
                "QLabel{color:#F7F9FC;}"
            )

            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 20, 24, 20)
            layout.setSpacing(16)

            title = QLabel("Source movie file is missing", self)
            title.setStyleSheet("font-size:18px;font-weight:700;color:#EF4444;")
            layout.addWidget(title)

            sub = QLabel(f"Previous location:\n{missing_file_path}", self)
            sub.setStyleSheet("font-size:12px;color:#A9B2C3;font-family:'Cascadia Code';")
            sub.setWordWrap(True)
            layout.addWidget(sub)

            btns = QHBoxLayout()
            btns.setSpacing(10)

            browse_btn = QPushButton("Locate File…", self)
            browse_btn.setFixedHeight(36)
            browse_btn.setProperty("primary", "true")
            browse_btn.clicked.connect(self._locate)
            btns.addWidget(browse_btn)

            search_btn = QPushButton("Search Folder…", self)
            search_btn.setFixedHeight(36)
            btns.addWidget(search_btn)

            offline_btn = QPushButton("Open Offline", self)
            offline_btn.setFixedHeight(36)
            offline_btn.clicked.connect(self.reject)
            btns.addWidget(offline_btn)

            layout.addLayout(btns)

        def _locate(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Locate Source Video", "", "Video Files (*.mkv *.mp4 *.mov);;All Files (*)"
            )
            if path:
                self.relinquished_path = path
                self.accept()


__all__ = ["CrashRecoveryDialog", "MissingFileRelinkDialog"]
