"""Cancellable, resumable job descriptors and their explicit state machine."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import Field, JsonValue, model_validator

from .artifact import ArtifactType
from .base import DomainModel, InvalidStateTransition, UtcDatetime, normalize_utc, utc_now
from .identifiers import ArtifactId, JobId, LocalizationId, ProjectId, SceneId, UtteranceId
from .types import NonEmptyStr, require_unique


class JobStatus(StrEnum):
    QUEUED = "queued"
    BLOCKED = "blocked"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    STALE = "stale"

    @property
    def terminal(self) -> bool:
        return self in {self.CANCELLED, self.FAILED, self.SUCCEEDED}


class JobPriority(StrEnum):
    BACKGROUND = "background"
    NORMAL = "normal"
    INTERACTIVE = "interactive"
    URGENT = "urgent"


class JobErrorCategory(StrEnum):
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_MEDIA = "unsupported_media"
    RIGHTS_POLICY = "rights_policy"
    PROVIDER_AUTH = "provider_auth"
    PROVIDER_QUOTA = "provider_quota"
    PROVIDER_TRANSIENT = "provider_transient"
    ENGINE_FAILURE = "engine_failure"
    GPU_OUT_OF_MEMORY = "gpu_out_of_memory"
    DISK_FULL = "disk_full"
    WORKER_CRASH = "worker_crash"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    INTERNAL = "internal"


class JobScope(DomainModel):
    localization_id: LocalizationId | None = None
    scene_id: SceneId | None = None
    utterance_id: UtteranceId | None = None


class ResourceRequest(DomainModel):
    cpu_cores: float = Field(default=1.0, gt=0.0, le=256.0, allow_inf_nan=False)
    ram_mib: int = Field(default=512, ge=0)
    vram_mib: int = Field(default=0, ge=0)
    scratch_mib: int = Field(default=0, ge=0)
    gpu_count: int = Field(default=0, ge=0, le=16)
    network_required: bool = False
    provider_quota_units: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_resources(self) -> Self:
        if self.vram_mib > 0 and self.gpu_count == 0:
            raise ValueError("VRAM reservation requires at least one GPU")
        if self.gpu_count > 0 and self.vram_mib == 0:
            raise ValueError("GPU reservation requires an explicit VRAM amount")
        if any(not key.strip() or value <= 0 for key, value in self.provider_quota_units.items()):
            raise ValueError("provider quota names must be non-empty and values must be positive")
        return self


class RetryPolicy(DomainModel):
    max_attempts: int = Field(default=3, ge=1, le=100)
    initial_backoff_ms: int = Field(default=1_000, ge=0, le=86_400_000)
    max_backoff_ms: int = Field(default=60_000, ge=0, le=86_400_000)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0, allow_inf_nan=False)
    retryable_categories: frozenset[JobErrorCategory] = frozenset(
        {
            JobErrorCategory.PROVIDER_TRANSIENT,
            JobErrorCategory.GPU_OUT_OF_MEMORY,
            JobErrorCategory.WORKER_CRASH,
            JobErrorCategory.TIMEOUT,
        }
    )

    @model_validator(mode="after")
    def _validate_backoff(self) -> Self:
        if self.max_backoff_ms < self.initial_backoff_ms:
            raise ValueError("maximum backoff cannot be smaller than initial backoff")
        return self


class JobProgress(DomainModel):
    completed_units: int = Field(default=0, ge=0)
    total_units: int = Field(default=1, gt=0)
    unit_name: NonEmptyStr = "items"
    message: str = Field(default="", max_length=1_000)

    @model_validator(mode="after")
    def _validate_progress(self) -> Self:
        if self.completed_units > self.total_units:
            raise ValueError("completed progress cannot exceed total progress")
        return self

    @property
    def fraction(self) -> float:
        return self.completed_units / self.total_units


class JobError(DomainModel):
    category: JobErrorCategory
    code: NonEmptyStr
    message: NonEmptyStr
    retryable: bool
    remediation_hint: NonEmptyStr | None = None
    diagnostics: dict[str, JsonValue] = Field(default_factory=dict)


_ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset(
        {
            JobStatus.BLOCKED,
            JobStatus.PREPARING,
            JobStatus.CANCELLING,
            JobStatus.CANCELLED,
            JobStatus.STALE,
        }
    ),
    JobStatus.BLOCKED: frozenset(
        {JobStatus.QUEUED, JobStatus.CANCELLING, JobStatus.CANCELLED, JobStatus.STALE}
    ),
    JobStatus.PREPARING: frozenset(
        {JobStatus.RUNNING, JobStatus.CANCELLING, JobStatus.FAILED, JobStatus.STALE}
    ),
    JobStatus.RUNNING: frozenset(
        {
            JobStatus.PAUSING,
            JobStatus.CANCELLING,
            JobStatus.FAILED,
            JobStatus.SUCCEEDED,
            JobStatus.STALE,
        }
    ),
    JobStatus.PAUSING: frozenset(
        {JobStatus.PAUSED, JobStatus.CANCELLING, JobStatus.FAILED, JobStatus.STALE}
    ),
    JobStatus.PAUSED: frozenset(
        {
            JobStatus.QUEUED,
            JobStatus.PREPARING,
            JobStatus.CANCELLING,
            JobStatus.CANCELLED,
            JobStatus.STALE,
        }
    ),
    JobStatus.CANCELLING: frozenset({JobStatus.CANCELLED, JobStatus.FAILED}),
    JobStatus.CANCELLED: frozenset({JobStatus.QUEUED, JobStatus.STALE}),
    JobStatus.FAILED: frozenset({JobStatus.QUEUED, JobStatus.STALE}),
    JobStatus.SUCCEEDED: frozenset({JobStatus.STALE}),
    JobStatus.STALE: frozenset({JobStatus.QUEUED}),
}


def can_transition_job_status(current: JobStatus, target: JobStatus) -> bool:
    """Return whether the canonical job state machine permits a distinct next state.

    This pure policy function is the single integration point for persistence and orchestration.
    Persisting the same state may be treated as an idempotent update by those layers; it is not a
    domain transition and therefore returns ``False`` here.
    """

    return current is not target and target in _ALLOWED_TRANSITIONS[current]


class Job(DomainModel):
    """Persistable job node. Mutation helpers return a newly validated revision."""

    job_id: JobId
    project_id: ProjectId
    job_type: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,127}$")
    idempotency_key: str = Field(min_length=8, max_length=256)
    scope: JobScope = Field(default_factory=JobScope)
    input_artifact_ids: tuple[ArtifactId, ...] = ()
    expected_output_types: tuple[ArtifactType, ...]
    dependency_job_ids: tuple[JobId, ...] = ()
    resource_request: ResourceRequest = Field(default_factory=ResourceRequest)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.QUEUED
    attempt: int = Field(default=0, ge=0)
    progress: JobProgress = Field(default_factory=JobProgress)
    checkpoint_interval_seconds: int = Field(default=10, gt=0, le=3_600)
    cancellation_safe_boundaries: tuple[NonEmptyStr, ...] = ("item",)
    deadline: UtcDatetime | None = None
    checkpoint: dict[str, JsonValue] | None = None
    error: JobError | None = None
    created_at: UtcDatetime = Field(default_factory=utc_now)
    updated_at: UtcDatetime = Field(default_factory=utc_now)
    started_at: UtcDatetime | None = None
    finished_at: UtcDatetime | None = None

    @model_validator(mode="after")
    def _validate_job(self) -> Self:
        require_unique(self.input_artifact_ids, field_name="input_artifact_ids")
        require_unique(self.expected_output_types, field_name="expected_output_types")
        require_unique(self.dependency_job_ids, field_name="dependency_job_ids")
        require_unique(
            self.cancellation_safe_boundaries,
            field_name="cancellation_safe_boundaries",
        )
        if self.job_id in self.dependency_job_ids:
            raise ValueError("job cannot depend on itself")
        if not self.expected_output_types:
            raise ValueError("job must declare at least one expected output type")
        if not self.cancellation_safe_boundaries:
            raise ValueError("job must declare a cancellation-safe boundary")
        if self.attempt > self.retry_policy.max_attempts:
            raise ValueError("job attempts exceed retry policy")
        if self.updated_at < self.created_at:
            raise ValueError("job update timestamp cannot precede creation")
        if self.deadline is not None and self.deadline < self.created_at:
            raise ValueError("job deadline cannot precede creation")
        if self.started_at is not None and self.started_at < self.created_at:
            raise ValueError("job start cannot precede creation")
        if self.finished_at is not None:
            baseline = self.started_at or self.created_at
            if self.finished_at < baseline:
                raise ValueError("job finish cannot precede start")
        if self.status.terminal and self.finished_at is None:
            raise ValueError("terminal job requires a finish timestamp")
        if not self.status.terminal and self.finished_at is not None:
            raise ValueError("non-terminal job cannot have a finish timestamp")
        started_states = {
            JobStatus.RUNNING,
            JobStatus.PAUSING,
            JobStatus.PAUSED,
            JobStatus.SUCCEEDED,
        }
        if self.status in started_states and self.started_at is None:
            raise ValueError(f"{self.status.value} job requires a start timestamp")
        if self.status is JobStatus.FAILED and self.error is None:
            raise ValueError("failed job requires a structured error")
        if self.status is not JobStatus.FAILED and self.error is not None:
            raise ValueError("only failed jobs may carry a terminal error")
        if (
            self.status is JobStatus.SUCCEEDED
            and self.progress.completed_units != self.progress.total_units
        ):
            raise ValueError("successful job must report complete progress")
        return self

    def can_transition_to(self, status: JobStatus) -> bool:
        return can_transition_job_status(self.status, status)

    def transition_to(
        self,
        status: JobStatus,
        *,
        at: datetime | None = None,
        error: JobError | None = None,
    ) -> Job:
        """Return the next immutable job state or reject an invalid transition."""

        if not self.can_transition_to(status):
            raise InvalidStateTransition(f"cannot transition job from {self.status} to {status}")
        instant = normalize_utc(at or utc_now())
        if instant < self.updated_at:
            raise ValueError("job transition timestamp cannot move backwards")
        changes: dict[str, object] = {
            "status": status,
            "updated_at": instant,
            "error": None,
        }

        if status is JobStatus.RUNNING:
            changes["started_at"] = self.started_at or instant
            changes["attempt"] = self.attempt + 1
        if status.terminal:
            changes["finished_at"] = instant
        elif self.status.terminal:
            changes["finished_at"] = None
        if status is JobStatus.FAILED:
            if error is None:
                raise ValueError("failed transition requires a structured error")
            changes["error"] = error
        elif error is not None:
            raise ValueError("error can only accompany a failed transition")
        if status is JobStatus.SUCCEEDED:
            changes["progress"] = self.progress.model_copy(
                update={"completed_units": self.progress.total_units}
            )

        payload = self.model_dump(mode="python")
        payload.update(changes)
        return Job.model_validate(payload)


__all__ = [
    "Job",
    "JobError",
    "JobErrorCategory",
    "JobPriority",
    "JobProgress",
    "JobScope",
    "JobStatus",
    "ResourceRequest",
    "RetryPolicy",
    "can_transition_job_status",
]
