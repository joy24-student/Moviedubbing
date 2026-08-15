"""Typed records shared by the SQLite project persistence APIs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

JsonObject = Mapping[str, Any]


def utc_now() -> str:
    """Return an RFC 3339 timestamp in UTC with microsecond precision."""

    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


class JobState(StrEnum):
    QUEUED = "QUEUED"
    BLOCKED = "BLOCKED"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    STALE = "STALE"


class ArtifactStatus(StrEnum):
    READY = "READY"
    MISSING = "MISSING"
    CORRUPT = "CORRUPT"
    QUARANTINED = "QUARANTINED"


class ReproducibilityLevel(StrEnum):
    EXACT = "EXACT"
    BEST_EFFORT = "BEST_EFFORT"
    NON_REPRODUCIBLE = "NON_REPRODUCIBLE"


@dataclass(frozen=True, slots=True)
class ProjectRecord:
    id: str
    name: str
    source_language: str | None = None
    settings: JsonObject = field(default_factory=dict)
    state: str = "ACTIVE"
    created_at: str | None = None
    updated_at: str | None = None
    revision: int = 0


@dataclass(frozen=True, slots=True)
class JobRecord:
    id: str
    project_id: str
    job_type: str
    idempotency_key: str
    state: JobState = JobState.QUEUED
    priority: int = 0
    progress: float = 0.0
    scope: JsonObject = field(default_factory=dict)
    inputs: JsonObject = field(default_factory=dict)
    expected_outputs: JsonObject = field(default_factory=dict)
    resource_request: JsonObject = field(default_factory=dict)
    checkpoint: JsonObject | None = None
    retry_count: int = 0
    max_retries: int = 0
    error_category: str | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    id: str
    project_id: str
    sha256: str
    byte_length: int
    relative_path: str
    logical_type: str
    media_type: str | None = None
    status: ArtifactStatus = ArtifactStatus.READY
    metadata: JsonObject = field(default_factory=dict)
    engine_id: str | None = None
    engine_version: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    model_weight_sha256: str | None = None
    parameters: JsonObject = field(default_factory=dict)
    prompt_version: str | None = None
    provider_id: str | None = None
    hardware: JsonObject = field(default_factory=dict)
    quality_metrics: JsonObject = field(default_factory=dict)
    seed: int | None = None
    reproducibility_level: ReproducibilityLevel = ReproducibilityLevel.BEST_EFFORT
    created_by: str | None = None
    created_at: str | None = None


@dataclass(frozen=True, slots=True)
class AuditEventRecord:
    id: str
    project_id: str
    action: str
    actor_type: str
    actor_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    job_id: str | None = None
    artifact_id: str | None = None
    correlation_id: str | None = None
    details: JsonObject = field(default_factory=dict)
    occurred_at: str | None = None


@dataclass(frozen=True, slots=True)
class MigrationInfo:
    version: int
    name: str
    checksum: str
    applied_at: str


@dataclass(frozen=True, slots=True)
class MigrationReport:
    previous_version: int
    current_version: int
    applied_versions: tuple[int, ...]
    backup_path: str | None = None


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    database_ok: bool
    messages: tuple[str, ...]
    foreign_key_violations: tuple[tuple[Any, ...], ...]
