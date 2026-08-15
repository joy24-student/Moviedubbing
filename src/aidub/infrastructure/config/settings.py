"""Typed non-secret application configuration."""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aidub.security.privacy import NetworkPolicy


class PerformanceMode(StrEnum):
    ECO = "eco"
    BALANCED = "balanced"
    PERFORMANCE = "performance"
    MAXIMUM = "maximum"


class QualityPreset(StrEnum):
    DRAFT = "draft"
    FAST = "fast"
    PROFESSIONAL = "professional"
    CINEMA = "cinema"
    OFFLINE_PRIVATE = "offline_private"


def default_application_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "AIDubbingStudio"
    return Path.home() / ".local" / "share" / "aidub-studio"


class SettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class StorageSettings(SettingsModel):
    projects: Path = Field(default_factory=lambda: default_application_root() / "Projects")
    cache: Path = Field(default_factory=lambda: default_application_root() / "Cache")
    models: Path = Field(default_factory=lambda: default_application_root() / "Models")
    temporary: Path = Field(default_factory=lambda: default_application_root() / "Temp")
    logs: Path = Field(default_factory=lambda: default_application_root() / "Logs")
    maximum_cache_gb: int = Field(default=100, ge=1, le=100_000)
    minimum_free_space_gb: int = Field(default=20, ge=1, le=10_000)

    @field_validator("projects", "cache", "models", "temporary", "logs")
    @classmethod
    def absolute_paths(cls, value: Path) -> Path:
        path = value.expanduser()
        if not path.is_absolute():
            raise ValueError("storage paths must be absolute")
        return path

    def ensure_directories(self) -> None:
        for path in (
            self.projects,
            self.cache,
            self.models,
            self.temporary,
            self.logs,
        ):
            path.mkdir(parents=True, exist_ok=True)


class ApplicationSettings(SettingsModel):
    schema_version: int = Field(default=1, ge=1)
    locale: str = Field(default="en", pattern=r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
    autosave_seconds: int = Field(default=30, ge=5, le=3600)
    network_policy: NetworkPolicy = NetworkPolicy.OFFLINE
    performance_mode: PerformanceMode = PerformanceMode.BALANCED
    quality_preset: QualityPreset = QualityPreset.PROFESSIONAL
    worker_count: int = Field(default=2, ge=1, le=64)
    preferred_gpu_ids: tuple[int, ...] = ()
    vram_reserve_mb: int = Field(default=1024, ge=0, le=262_144)
    telemetry_enabled: bool = False
    storage: StorageSettings = Field(default_factory=StorageSettings)

    @field_validator("preferred_gpu_ids")
    @classmethod
    def unique_nonnegative_gpu_ids(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(item < 0 for item in value):
            raise ValueError("GPU IDs must be nonnegative")
        if len(set(value)) != len(value):
            raise ValueError("GPU IDs must be unique")
        return value
