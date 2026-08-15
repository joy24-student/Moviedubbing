"""Strict Pydantic v2 payload schemas for LLM-generated structured outputs."""

from __future__ import annotations

from pydantic import Field

from aidub.contracts.base import ContractModel, Identifier
from aidub.domain.types import LanguageTag


class TranslationResult(ContractModel):
    """Structured output from a translation LLM pass."""

    source_text: str = Field(min_length=1, max_length=32_000)
    translated_text: str = Field(min_length=1, max_length=32_000)
    target_language: LanguageTag
    duration_estimate_ms: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    adaptation_notes: str = Field(default="", max_length=4_000)


class QCResult(ContractModel):
    """Structured QC evaluation output."""

    utterance_id: Identifier
    passed: bool
    issues: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)


class SceneSummary(ContractModel):
    """Scene context summary for translation prompts."""

    scene_id: Identifier
    location: str = Field(default="", max_length=256)
    time_of_day: str = Field(default="", max_length=64)
    tone: str = Field(default="", max_length=64)
    summary: str = Field(default="", max_length=2_000)


__all__ = ["QCResult", "SceneSummary", "TranslationResult"]
