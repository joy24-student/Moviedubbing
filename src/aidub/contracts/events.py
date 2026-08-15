"""Event envelopes emitted by jobs and workers."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from .base import ContractModel, Identifier, utc_now


class EventType(StrEnum):
    JOB_QUEUED = "job.queued"
    JOB_STARTED = "job.started"
    JOB_PROGRESS = "job.progress"
    JOB_CHECKPOINT = "job.checkpoint"
    JOB_PAUSED = "job.paused"
    JOB_CANCELLED = "job.cancelled"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    ARTIFACT_CREATED = "artifact.created"
    PROJECT_CHANGED = "project.changed"
    PROVIDER_HEALTH_CHANGED = "provider.health_changed"
    MODEL_LOADED = "model.loaded"
    MODEL_UNLOADED = "model.unloaded"
    QC_ISSUE_CREATED = "qc.issue_created"


class EventEnvelope(ContractModel):
    schema_version: int = Field(default=1, ge=1)
    event_id: Identifier
    event_type: EventType
    occurred_at: datetime = Field(default_factory=utc_now)
    source: Identifier
    project_id: Identifier | None = None
    job_id: Identifier | None = None
    correlation_id: Identifier | None = None
    sequence: int = Field(default=0, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)
