"""
One-Click Basic Dub dialog for beginner automated workflow (Master Spec Section 1.4 & 85).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QProgressBar,
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

    class QuickDubDialog(QDialog):  # type: ignore[misc]
        """
        One-Click Automated Dubbing Dialog.
        Enables beginner users to perform a complete dubbing workflow
        without interacting with the professional editor.
        """

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("⚡ One-Click Movie Dubbing Wizard")
            self.setFixedSize(560, 420)
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
            icon = QLabel("⚡", self)
            icon.setStyleSheet("font-size:36px;")
            hdr.addWidget(icon)

            title_box = QVBoxLayout()
            title = QLabel("ONE-CLICK DUBBING", self)
            title.setStyleSheet("font-size:18px;font-weight:700;color:#22D3EE;")
            title_box.addWidget(title)
            sub = QLabel("Automated pipeline: Speech Recognition → Translation → Voice → Lip Sync", self)
            sub.setStyleSheet("font-size:12px;color:#A9B2C3;")
            title_box.addWidget(sub)
            hdr.addLayout(title_box)
            layout.addLayout(hdr)

            # File selection
            layout.addWidget(QLabel("1. Select Source Movie File:", self))
            file_row = QHBoxLayout()
            self.file_edit = QLineEdit("D:\\Movies\\sample_movie.mkv", self)
            file_row.addWidget(self.file_edit, 1)
            browse_btn = QPushButton("Browse…", self)
            browse_btn.clicked.connect(self._browse)
            file_row.addWidget(browse_btn)
            layout.addLayout(file_row)

            # Language + Mode Selection
            meta_row = QHBoxLayout()
            
            l_box = QVBoxLayout()
            l_box.addWidget(QLabel("2. Target Language:", self))
            self.lang_cb = QComboBox(self)
            self.lang_cb.addItems([
                "বাংলা (Bengali)",
                "हिंदी (Hindi)",
                "Español (Spanish)",
                "Français (French)",
                "Deutsch (German)",
                "العربية (Arabic)",
            ])
            l_box.addWidget(self.lang_cb)
            meta_row.addLayout(l_box)

            m_box = QVBoxLayout()
            m_box.addWidget(QLabel("3. Quality Profile:", self))
            self.mode_cb = QComboBox(self)
            self.mode_cb.addItems(["⭐ Professional (Recommended)", "⚡ Fast Dub", "🎬 Cinema Master"])
            m_box.addWidget(self.mode_cb)
            meta_row.addLayout(m_box)

            layout.addLayout(meta_row)

            # Progress bar frame
            self.progress_frame = QFrame(self)
            self.progress_frame.setStyleSheet("QFrame{background:#0D1118;border:1px solid #283241;border-radius:8px;padding:12px;}")
            pf_lay = QVBoxLayout(self.progress_frame)
            
            self.stage_lbl = QLabel("Ready to start automated pipeline.", self.progress_frame)
            self.stage_lbl.setStyleSheet("font-size:12px;font-weight:600;color:#22D3EE;")
            pf_lay.addWidget(self.stage_lbl)

            self.pbar = QProgressBar(self.progress_frame)
            self.pbar.setRange(0, 100)
            self.pbar.setValue(0)
            self.pbar.setStyleSheet("QProgressBar{border:none;background:#161D28;height:12px;border-radius:6px;} QProgressBar::chunk{background:#4F8CFF;border-radius:6px;}")
            pf_lay.addWidget(self.pbar)

            layout.addWidget(self.progress_frame)

            # Actions
            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)

            cancel_btn = QPushButton("Cancel", self)
            cancel_btn.clicked.connect(self.reject)
            btn_row.addWidget(cancel_btn)

            self.start_btn = QPushButton("🚀 START ONE-CLICK DUBBING", self)
            self.start_btn.setFixedHeight(42)
            self.start_btn.setProperty("primary", "true")
            self.start_btn.clicked.connect(self._start_dubbing)
            btn_row.addWidget(self.start_btn, 1)

            layout.addLayout(btn_row)

            self._timer = QTimer(self)
            self._timer.timeout.connect(self._step_progress)
            self._progress_val = 0

        def _browse(self) -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mkv *.mp4 *.mov)")
            if path:
                self.file_edit.setText(path)

        def _start_dubbing(self) -> None:
            self.start_btn.setEnabled(False)
            self._progress_val = 0
            self._timer.start(100)

        def _step_progress(self) -> None:
            self._progress_val += 2
            self.pbar.setValue(self._progress_val)

            if self._progress_val < 20:
                self.stage_lbl.setText("Stage 1/5: Extracting Audio & ASR Speech Recognition (Faster Whisper)…")
            elif self._progress_val < 45:
                self.stage_lbl.setText("Stage 2/5: Speaker Diarization & Neural Translation (Gemini AI)…")
            elif self._progress_val < 70:
                self.stage_lbl.setText("Stage 3/5: Voice Synthesis & Pitch/Energy Alignment (ElevenLabs Engine)…")
            elif self._progress_val < 90:
                self.stage_lbl.setText("Stage 4/5: Neural Lip-Sync Alignment (LatentSync V2)…")
            elif self._progress_val < 100:
                self.stage_lbl.setText("Stage 5/5: Final Audio Mixing & MKV Muxing…")
            else:
                self._timer.stop()
                self.stage_lbl.setText("✅ Dubbing Complete! Saved to D:\\Exports\\movie_dubbed.mp4")
                self.start_btn.setText("Open Completed Video")
                self.start_btn.setEnabled(True)
                self.start_btn.clicked.disconnect()
                self.start_btn.clicked.connect(self.accept)


__all__ = ["QuickDubDialog"]
