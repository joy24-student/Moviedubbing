"""Central network and data-disclosure policy.

All provider and telemetry clients must ask this policy before network I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class NetworkPolicy(StrEnum):
    OFFLINE = "offline"
    HYBRID = "hybrid"
    CLOUD_ASSISTED = "cloud_assisted"
    STUDIO_LOCKED = "studio_locked"


class DataClass(StrEnum):
    TELEMETRY = "telemetry"
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason_code: str


@dataclass(frozen=True, slots=True)
class PrivacyPolicy:
    network: NetworkPolicy = NetworkPolicy.OFFLINE
    allowed_providers: frozenset[str] = frozenset()
    allowed_data_classes: frozenset[DataClass] = frozenset()
    telemetry_enabled: bool = False
    locked: bool = False

    def evaluate(
        self,
        *,
        provider_id: str,
        data_class: DataClass,
        is_telemetry: bool = False,
    ) -> PolicyDecision:
        if self.network == NetworkPolicy.OFFLINE:
            return PolicyDecision(allowed=False, reason_code="privacy.offline_blocks_network")
        if is_telemetry and not self.telemetry_enabled:
            return PolicyDecision(allowed=False, reason_code="privacy.telemetry_disabled")
        if provider_id not in self.allowed_providers:
            return PolicyDecision(allowed=False, reason_code="privacy.provider_not_allowed")
        if data_class not in self.allowed_data_classes:
            return PolicyDecision(allowed=False, reason_code="privacy.data_class_not_allowed")
        return PolicyDecision(allowed=True, reason_code="privacy.allowed")

    def require(
        self,
        *,
        provider_id: str,
        data_class: DataClass,
        is_telemetry: bool = False,
    ) -> None:
        decision = self.evaluate(
            provider_id=provider_id,
            data_class=data_class,
            is_telemetry=is_telemetry,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason_code)
