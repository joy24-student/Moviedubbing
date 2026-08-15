"""Provider-neutral language/reasoning contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from .base import (
    ContractModel,
    HealthState,
    Identifier,
    LocaleCode,
    Sha256,
    utc_now,
)


class ProviderCapability(StrEnum):
    TRANSLATION = "translation"
    DURATION_REWRITE = "duration_rewrite"
    CULTURAL_ADAPTATION = "cultural_adaptation"
    TRANSLATION_CRITIQUE = "translation_critique"
    SCENE_SUMMARY = "scene_summary"
    QC_EXPLANATION = "qc_explanation"
    STRUCTURED_OUTPUT = "structured_output"


class ProviderTask(StrEnum):
    TRANSLATE = "translate"
    ADAPT = "adapt"
    FIT_DURATION = "fit_duration"
    CRITIQUE = "critique"
    SUMMARIZE_SCENE = "summarize_scene"
    EXPLAIN_QC = "explain_qc"


class ProviderHealth(ContractModel):
    provider_id: Identifier
    state: HealthState
    checked_at: datetime = Field(default_factory=utc_now)
    latency_ms: int | None = Field(default=None, ge=0)
    recent_failure_rate: float = Field(default=0, ge=0, le=1)
    capabilities: frozenset[ProviderCapability] = frozenset()
    reason_code: Identifier | None = None


class TranslationContext(ContractModel):
    previous_lines: tuple[str, ...] = ()
    next_lines: tuple[str, ...] = ()
    character: dict[str, Any] = Field(default_factory=dict)
    scene: dict[str, Any] = Field(default_factory=dict)
    glossary: dict[str, str] = Field(default_factory=dict)


class ProviderConstraints(ContractModel):
    target_duration_ms: int | None = Field(default=None, gt=0)
    maximum_duration_error_percent: float = Field(default=8.0, gt=0, le=100)
    preserve_names: bool = True
    content_rating: str | None = Field(default=None, max_length=40)
    response_schema: Identifier


class ProviderRequest(ContractModel):
    request_id: Identifier
    task: ProviderTask
    project_id: Identifier
    utterance_id: Identifier | None = None
    source_language: LocaleCode
    target_language: LocaleCode
    source_text: str = Field(min_length=1, max_length=100_000)
    context: TranslationContext = Field(default_factory=TranslationContext)
    constraints: ProviderConstraints
    prompt_id: Identifier
    prompt_version: Identifier
    request_hash: Sha256


class ProviderUsage(ContractModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_microunits: int | None = Field(default=None, ge=0)


class ProviderResponse(ContractModel):
    request_id: Identifier
    provider_id: Identifier
    model_id: Identifier
    response_hash: Sha256
    received_at: datetime = Field(default_factory=utc_now)
    latency_ms: int = Field(ge=0)
    retry_count: int = Field(default=0, ge=0)
    structured_output: dict[str, Any]
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    degraded: bool = False
    warnings: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def output_cannot_be_empty(self) -> ProviderResponse:
        if not self.structured_output:
            raise ValueError("provider structured_output cannot be empty")
        return self
