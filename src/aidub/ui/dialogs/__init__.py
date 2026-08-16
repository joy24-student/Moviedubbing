"""Production dialog windows for AI Movie Dubbing Studio."""

from __future__ import annotations

from aidub.ui.dialogs.ai_fix_dialog import AiFixAllDialog
from aidub.ui.dialogs.character_dialogs import AssignVoiceDialog, MergeSpeakerDialog, SplitSpeakerDialog
from aidub.ui.dialogs.quick_dub_dialog import QuickDubDialog
from aidub.ui.dialogs.recovery_dialog import CrashRecoveryDialog, MissingFileRelinkDialog

__all__ = [
    "AiFixAllDialog",
    "AssignVoiceDialog",
    "CrashRecoveryDialog",
    "MergeSpeakerDialog",
    "MissingFileRelinkDialog",
    "QuickDubDialog",
    "SplitSpeakerDialog",
]
