"""Safe source-caption ingestion into deterministic transcript candidates."""

from .errors import (
    SubtitleIngestionConflictError,
    SubtitleIngestionError,
    UnsafeSubtitleSourceError,
    UnsupportedSubtitleEncodingError,
)
from .models import (
    SourceSubtitleProvenance,
    SubtitleIngestionReport,
    SubtitleIngestionRequest,
    SubtitleIngestionResult,
    SubtitleSourceEncoding,
    SubtitleTimingConflict,
    SubtitleTimingConflictCode,
    SubtitleTimingConflictSeverity,
    SubtitleUtteranceCandidate,
)
from .service import SourceSubtitleIngestionService, ingest_source_subtitle

__all__ = [
    "SourceSubtitleIngestionService",
    "SourceSubtitleProvenance",
    "SubtitleIngestionConflictError",
    "SubtitleIngestionError",
    "SubtitleIngestionReport",
    "SubtitleIngestionRequest",
    "SubtitleIngestionResult",
    "SubtitleSourceEncoding",
    "SubtitleTimingConflict",
    "SubtitleTimingConflictCode",
    "SubtitleTimingConflictSeverity",
    "SubtitleUtteranceCandidate",
    "UnsafeSubtitleSourceError",
    "UnsupportedSubtitleEncodingError",
    "ingest_source_subtitle",
]
