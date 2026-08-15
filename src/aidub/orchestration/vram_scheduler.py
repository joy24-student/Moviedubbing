"""VRAM-aware GPU model scheduler for multi-tier hardware planning."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from aidub.contracts.base import ContractModel
from aidub.infrastructure.models.manager import ModelDescriptor, ModelManager

logger = logging.getLogger(__name__)

# Hardware tier VRAM budgets in MiB
TIER_8GB_VRAM_MB = 8_192
TIER_16GB_VRAM_MB = 16_384
TIER_24GB_VRAM_MB = 24_576


class GpuTier(StrEnum):
    TIER_8GB = "8gb"
    TIER_16GB = "16gb"
    TIER_24GB_PLUS = "24gb_plus"


class VramSchedulerPolicy(ContractModel):
    """Configurable VRAM scheduling policy per GPU hardware tier."""

    gpu_tier: GpuTier = GpuTier.TIER_16GB
    safety_margin_mb: int = Field(default=512, ge=0, le=4_096)

    @model_validator(mode="after")
    def _validate(self) -> Self:
        return self

    @property
    def total_budget_mb(self) -> int:
        budgets = {
            GpuTier.TIER_8GB: TIER_8GB_VRAM_MB,
            GpuTier.TIER_16GB: TIER_16GB_VRAM_MB,
            GpuTier.TIER_24GB_PLUS: TIER_24GB_VRAM_MB,
        }
        return budgets[self.gpu_tier]

    @property
    def usable_budget_mb(self) -> int:
        return max(0, self.total_budget_mb - self.safety_margin_mb)


class VramBudgetExceededError(RuntimeError):
    """Raised when loading a model would exceed the available VRAM budget."""

    def __init__(self, model_id: str, required_mb: int, available_mb: int) -> None:
        super().__init__(
            f"loading {model_id!r} requires {required_mb}MB VRAM but only {available_mb}MB available"
        )
        self.model_id = model_id
        self.required_mb = required_mb
        self.available_mb = available_mb


class VramScheduler:
    """
    GPU VRAM-aware model scheduler.

    Tracks loaded model VRAM consumption and evicts lowest-priority
    models to make room for higher-priority model loads. Enforces
    strict hardware tier budget caps.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        policy: VramSchedulerPolicy | None = None,
    ) -> None:
        self._manager = model_manager
        self._policy = policy or VramSchedulerPolicy()

    @property
    def policy(self) -> VramSchedulerPolicy:
        return self._policy

    def available_vram_mb(self) -> int:
        """Return VRAM available within the current budget."""
        used = self._manager.registered_vram_mb()
        return max(0, self._policy.usable_budget_mb - used)

    def can_load(self, descriptor: ModelDescriptor) -> bool:
        """Return True if loading this model fits within available VRAM budget."""
        return descriptor.vram_mb <= self.available_vram_mb()

    def schedule_load(self, model_id: str, *, evict_if_needed: bool = True) -> ModelDescriptor:
        """
        Load a model, optionally evicting lower-priority warm models to free VRAM.

        Args:
            model_id: Registered model ID.
            evict_if_needed: If True, evict lowest-priority loaded models to make room.

        Raises:
            VramBudgetExceededError: If the model cannot fit even after eviction.
        """
        entry = self._manager.get_entry(model_id)
        if entry is None:
            raise KeyError(f"model {model_id!r} is not registered with the model manager")

        descriptor = entry.descriptor

        # Already loaded — no-op
        if entry.status.value == "loaded":
            return descriptor

        if not self.can_load(descriptor):
            if evict_if_needed:
                self._evict_for(descriptor.vram_mb, descriptor.load_priority)
            if not self.can_load(descriptor):
                available = self.available_vram_mb()
                raise VramBudgetExceededError(model_id, descriptor.vram_mb, available)

        return self._manager.load(model_id)

    def _evict_for(self, required_mb: int, priority: int) -> None:
        """Evict lowest-priority loaded models until required_mb VRAM is free."""
        loaded = sorted(
            self._manager.loaded_models(),
            key=lambda d: d.load_priority,
        )

        for descriptor in loaded:
            if descriptor.load_priority >= priority:
                # Do not evict equal or higher priority models
                break
            if self.available_vram_mb() >= required_mb:
                break
            logger.info(
                "vram_scheduler: evicting %s (priority=%s vram_mb=%s) to free space for new load",
                descriptor.model_id,
                descriptor.load_priority,
                descriptor.vram_mb,
            )
            self._manager.unload(descriptor.model_id)

    def unload(self, model_id: str) -> None:
        """Explicitly unload a model to free its VRAM budget."""
        self._manager.unload(model_id)


__all__ = [
    "TIER_8GB_VRAM_MB",
    "TIER_16GB_VRAM_MB",
    "TIER_24GB_VRAM_MB",
    "GpuTier",
    "VramBudgetExceededError",
    "VramScheduler",
    "VramSchedulerPolicy",
]
