"""
AI Fix All confirmation & batch preview dialog (Master Spec Section 45 & 68).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
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

    class AiFixAllDialog(QDialog):  # type: ignore[misc]
        """
        Batch AI Fix transaction preview & approval dialog.
        Shows exact count of target issues per dimension while guaranteeing
        that Approved and Locked lines remain protected.
        """

        def __init__(
            self,
            blocking_count: int = 4,
            warning_count: int = 18,
            parent: _W | None = None,
        ) -> None:
            super().__init__(parent)
            self.setWindowTitle("AI Fix All — Confirm Batch Operation")
            self.resize(520, 440)
            self.setModal(True)
            self.setStyleSheet(
                "QDialog{background:#161D28;border:1px solid #34415A;border-radius:12px;}"
                "QLabel{color:#F7F9FC;}"
            )

            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 20, 24, 20)
            layout.setSpacing(16)

            # Title & Header
            hdr = QHBoxLayout()
            icon = QLabel("🤖", self)
            icon.setStyleSheet("font-size:32px;")
            hdr.addWidget(icon)
            
            title_box = QVBoxLayout()
            title = QLabel("AI Fix All Operations", self)
            title.setStyleSheet("font-size:18px;font-weight:700;color:#F7F9FC;")
            title_box.addWidget(title)
            sub = QLabel("Automated batch resolution of non-locked defect items.", self)
            sub.setStyleSheet("font-size:12px;color:#A9B2C3;")
            title_box.addWidget(sub)
            hdr.addLayout(title_box)
            hdr.addStretch()
            layout.addLayout(hdr)

            # Protected badge frame
            prot_frame = QFrame(self)
            prot_frame.setStyleSheet(
                "QFrame{background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.3);"
                "border-radius:8px;padding:8px 12px;}"
            )
            pf_lay = QHBoxLayout(prot_frame)
            pf_lay.setContentsMargins(10, 6, 10, 6)
            lock_icon = QLabel("🔒", prot_frame)
            lock_icon.setStyleSheet("font-size:14px;")
            pf_lay.addWidget(lock_icon)
            lock_lbl = QLabel(
                "Protected: Approved and Locked lines will NOT be modified.",
                prot_frame,
            )
            lock_lbl.setStyleSheet("font-size:12px;font-weight:600;color:#22C55E;")
            pf_lay.addWidget(lock_lbl)
            pf_lay.addStretch()
            layout.addWidget(prot_frame)

            # Issue summary list
            layout.addWidget(QLabel("TARGET DEFECTS TO FIX:", self))

            self.issue_list = QListWidget(self)
            self.issue_list.setStyleSheet(
                "QListWidget{background:#0D1118;border:1px solid #283241;border-radius:8px;padding:4px;}"
                "QListWidget::item{padding:8px 10px;border-bottom:1px solid #161D28;}"
            )
            
            items = [
                ("⏱ 12 Timing Alignment issues", "Auto-shift and trim to within ±5% of original duration"),
                ("🌐 7 Translation phrasing issues", "Refine natural Bengali phrasing while maintaining length"),
                ("👄 4 Lip Sync alignment issues", "Apply LatentSync V2 model on active speaker frames"),
                ("🎙 3 Voice pitch drift issues", "Re-synthesize pitch curve to match reference profile"),
            ]
            
            for title_text, desc_text in items:
                item_widget = QWidget()
                iw_lay = QVBoxLayout(item_widget)
                iw_lay.setContentsMargins(0, 0, 0, 0)
                iw_lay.setSpacing(2)
                t_lbl = QLabel(title_text, item_widget)
                t_lbl.setStyleSheet("font-size:13px;font-weight:700;color:#4F8CFF;")
                iw_lay.addWidget(t_lbl)
                d_lbl = QLabel(desc_text, item_widget)
                d_lbl.setStyleSheet("font-size:11px;color:#A9B2C3;")
                iw_lay.addWidget(d_lbl)

                list_item = QListWidgetItem(self.issue_list)
                list_item.setSizeHint(item_widget.sizeHint())
                self.issue_list.addItem(list_item)
                self.issue_list.setItemWidget(list_item, item_widget)

            layout.addWidget(self.issue_list, 1)

            # Option checkbox
            self.create_snapshot_cb = QCheckBox("Create project undo snapshot before applying", self)
            self.create_snapshot_cb.setChecked(True)
            layout.addWidget(self.create_snapshot_cb)

            # Actions
            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)

            preview_btn = QPushButton("Preview Changes", self)
            preview_btn.setFixedHeight(36)
            btn_row.addWidget(preview_btn)

            btn_row.addStretch()

            cancel_btn = QPushButton("Cancel", self)
            cancel_btn.setFixedHeight(36)
            cancel_btn.clicked.connect(self.reject)
            btn_row.addWidget(cancel_btn)

            apply_btn = QPushButton("Apply Batch Fix (26 items)", self)
            apply_btn.setFixedHeight(36)
            apply_btn.setProperty("primary", "true")
            apply_btn.clicked.connect(self.accept)
            btn_row.addWidget(apply_btn)

            layout.addLayout(btn_row)


__all__ = ["AiFixAllDialog"]
