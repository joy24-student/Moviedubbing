"""Canonical job payloads and results."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from .base import ContractModel, Identifier, Sha256, utc_now


class JobPriority(StrEnum):
    BACKGROUND = "background"
    NORMAL = "normal"
    INTERACTIVE = "interactive"
    CRITICAL = "critical"


class ErrorCategory(StrEnum):
    INVALID_INPUT = "invalid_input"
    MEDIA = "media"
    STORAGE = "storage"
    DATABASE = "database"
    WORKER = "worker"
    GPU = "gpu"
    MODEL = "model"
    PROVIDER = "provider"
    POLICY = "policy"
    QUALITY = "quality"
    CANCELLED = "cancelled"
    INTERNAL = "internal"


class ResourceRequest(ContractModel):
    cpu_cores: float = Field(default=1.0, gt=0)
    ram_mb: int = Field(default=512, ge=64)
    gpu_count: int = Field(default=0, ge=0)
    vram_mb: int = Field(default=0, ge=0)
    scratch_mb: int = Field(default=256, ge=0)
    requires_network: bool = False
    compatible_gpu_ids: tuple[int, ...] = ()

    @model_validator(mode="after")
    def vram_requires_gpu(self) -> ResourceRequest:
        if self.vram_mb and self.gpu_count == 0:
            raise ValueError("vram_mb requires gpu_count greater than zero")
        return self


class RetryPolicy(ContractModel):
    maximum_attempts: int = Field(default=1, ge=1, le=10)
    initial_delay_ms: int = Field(default=500, ge=0, le=600_000)
    maximum_delay_ms: int = Field(default=30_000, ge=0, le=3_600_000)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0)
    jitter: bool = True

    @model_validator(mode="after")
    def delay_order(self) -> RetryPolicy:
        if self.maximum_delay_ms < self.initial_delay_ms:
            raise ValueError("maximum_delay_ms must be >= initial_delay_ms")
        return self


class ArtifactReference(ContractModel):
    artifact_id: Identifier
    sha256: Sha256
    media_type: str = Field(min_length=1, max_length=200)


class ArtifactExpectation(ContractModel):
    logical_name: Identifier
    artifact_type: Identifier
    media_type: str = Field(min_length=1, max_length=200)
    required: bool = True


class JobDescriptor(ContractModel):
    schema_version: int = Field(default=1, ge=1)
    job_id: Identifier
    idempotency_key: Sha256
    project_id: Identifier
    job_type: Identifier
    priority: JobPriority = JobPriority.NORMAL
    correlation_id: Identifier | None = None
    localization_id: Identifier | None = None
    scene_id: Identifier | None = None
    shot_id: Identifier | None = None
    utterance_id: Identifier | None = None
    dependencies: tuple[Identifier, ...] = ()
    resources: ResourceRequest = Field(default_factory=ResourceRequest)
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    inputs: tuple[ArtifactReference, ...] = ()
    outputs: tuple[ArtifactExpectation, ...] = ()
    parameters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def cannot_depend_on_self(self) -> JobDescriptor:
        if self.job_id in self.dependencies:
            raise ValueError("job cannot depend on itself")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("job dependencies must be unique")
        return self


class JobProgress(ContractModel):
    job_id: Identifier
    completed_units: int = Field(ge=0)
    total_units: int = Field(gt=0)
    unit_name: str = Field(default="items", min_length=1, max_length=80)
    message_key: Identifier | None = None
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def progress_in_bounds(self) -> JobProgress:
        if self.completed_units > self.total_units:
            raise ValueError("completed_units cannot exceed total_units")
        return self

    @property
    def fraction(self) -> float:
        return self.completed_units / self.total_units


class JobError(ContractModel):
    code: Identifier
    category: ErrorCategory
    retryable: bool
    message_key: Identifier
    safe_details: dict[str, str | int | float | bool] = Field(default_factory=dict)
    remediation_key: Identifier | None = None


class JobResult(ContractModel):
    job_id: Identifier
    succeeded: bool
    completed_at: datetime = Field(default_factory=utc_now)
    outputs: tuple[ArtifactReference, ...] = ()
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)
    error: JobError | None = None

    @model_validator(mode="after")
    def result_consistent(self) -> JobResult:
        if self.succeeded and self.error is not None:
            raise ValueError("successful job cannot contain an error")
        if not self.succeeded and self.error is None:
            raise ValueError("failed job must contain an error")
        return self
