"""Non-destructive transcript editing workflow."""

from .commands import (
    ApproveUtteranceCommand,
    AssignCharacterCommand,
    AssignSpeakerCommand,
    AutomatedAsrUpdateCommand,
    ChangeStatusCommand,
    EditTextCommand,
    LockFieldsCommand,
    MergePolicy,
    MergeUtterancesCommand,
    SplitUtteranceCommand,
    TranscriptCommand,
    UnlockFieldsCommand,
)
from .errors import (
    LockedFieldViolation,
    TranscriptError,
    TranscriptInvariantViolation,
    TranscriptRevisionConflict,
    UtteranceNotFound,
)
from .models import (
    InvalidationRoot,
    Transcript,
    TranscriptAuditFact,
    TranscriptMutationResult,
    TranscriptOperation,
    invalidation_key,
)
from .service import TranscriptCommandService

__all__ = [
    "ApproveUtteranceCommand",
    "AssignCharacterCommand",
    "AssignSpeakerCommand",
    "AutomatedAsrUpdateCommand",
    "ChangeStatusCommand",
    "EditTextCommand",
    "InvalidationRoot",
    "LockFieldsCommand",
    "LockedFieldViolation",
    "MergePolicy",
    "MergeUtterancesCommand",
    "SplitUtteranceCommand",
    "Transcript",
    "TranscriptAuditFact",
    "TranscriptCommand",
    "TranscriptCommandService",
    "TranscriptError",
    "TranscriptInvariantViolation",
    "TranscriptMutationResult",
    "TranscriptOperation",
    "TranscriptRevisionConflict",
    "UnlockFieldsCommand",
    "UtteranceNotFound",
    "invalidation_key",
]
