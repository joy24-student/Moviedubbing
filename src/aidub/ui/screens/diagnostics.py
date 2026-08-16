"""
Diagnostics Center screen (Master Spec Section 84).

Features:
- System runtime health matrix (Python, FFmpeg, CUDA, GPU, Models, Providers)
- Actions: Run Full Diagnostics, Export Diagnostic Report, Repair Runtime, Verify Models
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _QT = True
except ImportError:
    _QT = False

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget as _W


if _QT:

    class DiagnosticsScreen(QWidget):  # type: ignore[misc]
        """System & Runtime Diagnostics Workstation."""

        def __init__(self, parent: _W | None = None) -> None:
            super().__init__(parent)
            self.setObjectName("DiagnosticsScreen")
            self._build_ui()

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            root.setSpacing(12)

            # Header
            hdr = QHBoxLayout()
            title = QLabel("🛠️  DIAGNOSTICS CENTER", self)
            title.setObjectName("ScreenTitle")
            hdr.addWidget(title)

            hdr.addStretch()

            exp_btn = QPushButton("📄 Export Diagnostic Report", self)
            hdr.addWidget(exp_btn)

            run_btn = QPushButton("⚡ Run Full Diagnostics", self)
            run_btn.setProperty("primary", "true")
            hdr.addWidget(run_btn)

            root.addLayout(hdr)

            # Toolbar
            tbar = QFrame(self)
            tbar.setObjectName("Panel")
            t_lay = QHBoxLayout(tbar)
            t_lay.setContentsMargins(10, 8, 10, 8)
            t_lay.setSpacing(10)

            t_lay.addWidget(QPushButton("🔧 Repair Runtime", tbar))
            t_lay.addWidget(QPushButton("🔍 Verify Model Hashes", tbar))
            t_lay.addWidget(QPushButton("🔌 Test API Latencies", tbar))
            t_lay.addStretch()

            root.addWidget(tbar)

            # Diagnostics Table
            self.diag_table = QTableWidget(0, 4, self)
            self.diag_table.setHorizontalHeaderLabels([
                "Component",
                "Status",
                "Details / Version",
                "Recommended Action",
            ])
            self.diag_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.diag_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.diag_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.diag_table.setStyleSheet(
                "QTableWidget{background:#0D1118;gridline-color:#283241;border:1px solid #283241;}"
                "QHeaderView::section{background:#161D28;color:#A9B2C3;font-weight:700;padding:6px;border:none;}"
            )

            components = [
                ("Python Runtime", "✓ OK", "Python 3.12.2 (64-bit)", "None"),
                ("FFmpeg Audio/Video", "✓ OK", "FFmpeg 6.1.1-full_build (nvenc enabled)", "None"),
                ("FFprobe Metadata", "✓ OK", "FFprobe 6.1.1", "None"),
                ("NVIDIA CUDA", "✓ OK", "CUDA 12.2 • Driver 550.54", "None"),
                ("GPU Hardware", "✓ OK", "NVIDIA GeForce RTX 4070 (12 GB VRAM)", "None"),
                ("SQLite Database", "✓ OK", "SQLite 3.45.1 • WAL Mode Active", "None"),
                ("ASR Model (Whisper)", "✓ OK", "Whisper Large V3 (3.2 GB loaded)", "None"),
                ("Voice TTS Engine", "✓ OK", "Local Voice Synthesizer V2 (2.4 GB loaded)", "None"),
                ("Lip Sync Engine", "✓ OK", "LatentSync V2 (4.8 GB available)", "None"),
                ("Gemini Provider", "✓ OK", "Online • Latency 0.8s • Success 99%", "None"),
                ("ChatGPT Provider", "✓ OK", "Online • Latency 1.1s • Success 99%", "None"),
                ("DeepSeek Provider", "⚠ Warning", "High Latency (2.4s)", "Switch primary LLM to Gemini"),
            ]

            self.diag_table.setRowCount(len(components))
            for r, (comp, status, details, action) in enumerate(components):
                self.diag_table.setItem(r, 0, QTableWidgetItem(comp))
                s_item = QTableWidgetItem(status)
                if "OK" in status:
                    s_item.setForeground(Qt.GlobalColor.green)
                else:
                    s_item.setForeground(Qt.GlobalColor.yellow)
                self.diag_table.setItem(r, 1, s_item)
                self.diag_table.setItem(r, 2, QTableWidgetItem(details))
                self.diag_table.setItem(r, 3, QTableWidgetItem(action))

            root.addWidget(self.diag_table, 1)


__all__ = ["DiagnosticsScreen"]
