"""Stable, dependency-free schemas for performance and model benchmark evidence.

These dataclasses are deliberately separate from provider and engine adapters. Benchmark reports
must remain readable after an engine environment is removed, and creating an evidence record must
never import a GPU or model runtime.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import statistics
import struct
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Final

SCHEMA_VERSION: Final = 1


def _required_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _positive_finite(value: float, field_name: str, *, allow_zero: bool = False) -> None:
    lower_bound_ok = value >= 0 if allow_zero else value > 0
    if not math.isfinite(value) or not lower_bound_ok:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field_name} must be finite and {qualifier}")


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hexadecimal digest")


@dataclass(frozen=True, slots=True)
class MachineFingerprint:
    """Privacy-preserving execution environment identity.

    Hostnames, usernames, MAC addresses, disk serials, and paths are intentionally excluded.
    ``fingerprint_sha256`` identifies an equivalent runtime description; it is not a device ID.
    """

    system: str
    release: str
    machine: str
    processor: str
    pointer_bits: int
    python_implementation: str
    python_version: str
    logical_cpu_count: int
    fingerprint_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        for field_name in (
            "system",
            "release",
            "machine",
            "processor",
            "python_implementation",
            "python_version",
        ):
            _required_text(str(getattr(self, field_name)), field_name)
        if self.pointer_bits not in {32, 64}:
            raise ValueError("pointer_bits must be 32 or 64")
        if self.logical_cpu_count < 1:
            raise ValueError("logical_cpu_count must be positive")
        identity = self._identity_dict()
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        object.__setattr__(self, "fingerprint_sha256", hashlib.sha256(encoded).hexdigest())

    @classmethod
    def capture(cls) -> MachineFingerprint:
        """Capture only non-secret standard-library runtime attributes."""

        return cls(
            system=platform.system() or "unknown",
            release=platform.release() or "unknown",
            machine=platform.machine() or "unknown",
            processor=platform.processor() or "unknown",
            pointer_bits=struct.calcsize("P") * 8,
            python_implementation=platform.python_implementation(),
            python_version=platform.python_version(),
            logical_cpu_count=os.cpu_count() or 1,
        )

    def _identity_dict(self) -> dict[str, object]:
        return {
            "logical_cpu_count": self.logical_cpu_count,
            "machine": self.machine,
            "pointer_bits": self.pointer_bits,
            "processor": self.processor,
            "python_implementation": self.python_implementation,
            "python_version": self.python_version,
            "release": self.release,
            "system": self.system,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._identity_dict(), "fingerprint_sha256": self.fingerprint_sha256}


@dataclass(frozen=True, slots=True)
class PerformanceThresholds:
    """Explicit gates for one workload; Phase 0 values remain visibly provisional."""

    max_median_ms: float | None = None
    max_p95_ms: float | None = None
    min_throughput_items_per_second: float | None = None
    provisional: bool = True
    rationale: str = "Phase 0 provisional engineering gate"

    def __post_init__(self) -> None:
        if (
            self.max_median_ms is None
            and self.max_p95_ms is None
            and self.min_throughput_items_per_second is None
        ):
            raise ValueError("at least one benchmark threshold must be configured")
        for field_name in (
            "max_median_ms",
            "max_p95_ms",
            "min_throughput_items_per_second",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _positive_finite(value, field_name)
        if (
            self.max_median_ms is not None
            and self.max_p95_ms is not None
            and self.max_p95_ms < self.max_median_ms
        ):
            raise ValueError("max_p95_ms cannot be lower than max_median_ms")
        _required_text(self.rationale, "rationale")

    def to_dict(self) -> dict[str, object]:
        return {
            "max_median_ms": self.max_median_ms,
            "max_p95_ms": self.max_p95_ms,
            "min_throughput_items_per_second": self.min_throughput_items_per_second,
            "provisional": self.provisional,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkConfiguration:
    workload_name: str
    item_count: int
    warmups: int
    repetitions: int
    thresholds: PerformanceThresholds

    def __post_init__(self) -> None:
        _required_text(self.workload_name, "workload_name")
        if self.item_count < 1:
            raise ValueError("item_count must be positive")
        if self.warmups < 0:
            raise ValueError("warmups cannot be negative")
        if self.repetitions < 1:
            raise ValueError("repetitions must be positive")

    def to_dict(self) -> dict[str, object]:
        return {
            "item_count": self.item_count,
            "repetitions": self.repetitions,
            "thresholds": self.thresholds.to_dict(),
            "warmups": self.warmups,
            "workload_name": self.workload_name,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkSample:
    repetition: int
    elapsed_ns: int
    completed_items: int
    throughput_items_per_second: float

    def __post_init__(self) -> None:
        if self.repetition < 1:
            raise ValueError("repetition must be positive")
        if self.elapsed_ns < 1:
            raise ValueError("elapsed_ns must be positive")
        if self.completed_items < 1:
            raise ValueError("completed_items must be positive")
        _positive_finite(
            self.throughput_items_per_second,
            "throughput_items_per_second",
        )
        expected_throughput = self.completed_items * 1_000_000_000 / self.elapsed_ns
        if not math.isclose(
            self.throughput_items_per_second,
            expected_throughput,
            rel_tol=1e-12,
        ):
            raise ValueError("sample throughput does not match completed items and elapsed time")

    def to_dict(self) -> dict[str, object]:
        return {
            "completed_items": self.completed_items,
            "elapsed_ns": self.elapsed_ns,
            "repetition": self.repetition,
            "throughput_items_per_second": self.throughput_items_per_second,
        }


@dataclass(frozen=True, slots=True)
class ThresholdFailure:
    metric: str
    observed: float
    comparator: str
    threshold: float

    def __post_init__(self) -> None:
        _required_text(self.metric, "metric")
        if self.comparator not in {"<=", ">="}:
            raise ValueError("threshold comparator must be <= or >=")
        _positive_finite(self.observed, "observed", allow_zero=True)
        _positive_finite(self.threshold, "threshold")

    def to_dict(self) -> dict[str, object]:
        return {
            "comparator": self.comparator,
            "metric": self.metric,
            "observed": self.observed,
            "threshold": self.threshold,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """One complete benchmark result with all raw timing samples."""

    run_id: str
    started_at: datetime
    finished_at: datetime
    machine: MachineFingerprint
    configuration: BenchmarkConfiguration
    samples: tuple[BenchmarkSample, ...]
    median_ms: float
    p95_ms: float
    throughput_items_per_second: float
    threshold_failures: tuple[ThresholdFailure, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _required_text(self.run_id, "run_id")
        object.__setattr__(self, "started_at", _utc(self.started_at, "started_at"))
        object.__setattr__(self, "finished_at", _utc(self.finished_at, "finished_at"))
        if self.finished_at < self.started_at:
            raise ValueError("benchmark finish cannot precede start")
        if len(self.samples) != self.configuration.repetitions:
            raise ValueError("sample count must equal configured repetitions")
        if tuple(sample.repetition for sample in self.samples) != tuple(
            range(1, len(self.samples) + 1)
        ):
            raise ValueError("benchmark samples must have contiguous repetition numbers")
        for field_name in ("median_ms", "p95_ms", "throughput_items_per_second"):
            _positive_finite(float(getattr(self, field_name)), field_name)
        elapsed_values = tuple(sample.elapsed_ns for sample in self.samples)
        expected_median_ms = float(statistics.median(elapsed_values)) / 1_000_000
        expected_p95_ms = (
            sorted(elapsed_values)[math.ceil(0.95 * len(elapsed_values)) - 1] / 1_000_000
        )
        expected_throughput = (
            sum(sample.completed_items for sample in self.samples)
            * 1_000_000_000
            / sum(elapsed_values)
        )
        for field_name, observed, expected in (
            ("median_ms", self.median_ms, expected_median_ms),
            ("p95_ms", self.p95_ms, expected_p95_ms),
            ("throughput_items_per_second", self.throughput_items_per_second, expected_throughput),
        ):
            if not math.isclose(observed, expected, rel_tol=1e-12):
                raise ValueError(f"{field_name} does not match raw benchmark samples")
        if any(sample.completed_items != self.configuration.item_count for sample in self.samples):
            raise ValueError("every sample must complete the configured item count")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported benchmark schema version: {self.schema_version}")

    @property
    def passed(self) -> bool:
        return not self.threshold_failures

    def to_dict(self) -> dict[str, object]:
        return {
            "configuration": self.configuration.to_dict(),
            "finished_at": self.finished_at.isoformat(),
            "machine": self.machine.to_dict(),
            "median_ms": self.median_ms,
            "p95_ms": self.p95_ms,
            "passed": self.passed,
            "run_id": self.run_id,
            "samples": [sample.to_dict() for sample in self.samples],
            "schema_version": self.schema_version,
            "started_at": self.started_at.isoformat(),
            "threshold_failures": [failure.to_dict() for failure in self.threshold_failures],
            "throughput_items_per_second": self.throughput_items_per_second,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, sort_keys=True)


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    generated_at: datetime
    machine: MachineFingerprint
    results: tuple[BenchmarkResult, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _utc(self.generated_at, "generated_at"))
        if not self.results:
            raise ValueError("benchmark report must contain at least one result")
        if any(
            result.machine.fingerprint_sha256 != self.machine.fingerprint_sha256
            for result in self.results
        ):
            raise ValueError("all benchmark results must use the report machine fingerprint")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported benchmark schema version: {self.schema_version}")

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "machine": self.machine.to_dict(),
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
            "schema_version": self.schema_version,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, sort_keys=True)


class BenchmarkLanguage(StrEnum):
    ENGLISH = "en"
    BENGALI_BANGLADESH = "bn-BD"
    HINDI_INDIA = "hi-IN"


class ModelTask(StrEnum):
    ASR = "asr"
    DIARIZATION = "diarization"
    TRANSLATION = "translation"
    VOICE = "voice"
    TIMING = "timing"


class QualityMetricName(StrEnum):
    WER = "wer"
    CER = "cer"
    DER = "der"
    MOS = "mos"
    TIMING_ERROR_P95_MS = "timing_error_p95_ms"
    REQUESTS_PER_SECOND = "requests_per_second"


class MetricApplicability(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    NOT_MEASURED = "not_measured"


@dataclass(frozen=True, slots=True)
class QualityMetric:
    """A quality/throughput observation or an explicit reason why it has no value."""

    name: QualityMetricName
    applicability: MetricApplicability
    value: float | None = None
    sample_count: int | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if self.applicability is MetricApplicability.APPLICABLE:
            if self.value is None or self.sample_count is None:
                raise ValueError("applicable metric requires value and sample_count")
            _positive_finite(self.value, "metric value", allow_zero=True)
            if self.sample_count < 1:
                raise ValueError("metric sample_count must be positive")
            if self.name is QualityMetricName.MOS and not 1.0 <= self.value <= 5.0:
                raise ValueError("MOS must be between 1 and 5")
        else:
            if self.value is not None or self.sample_count is not None:
                raise ValueError(
                    "unmeasured/inapplicable metric cannot carry a value or sample count"
                )
            _required_text(self.notes, "metric notes")

    @property
    def unit(self) -> str:
        return {
            QualityMetricName.WER: "ratio",
            QualityMetricName.CER: "ratio",
            QualityMetricName.DER: "ratio",
            QualityMetricName.MOS: "score_1_to_5",
            QualityMetricName.TIMING_ERROR_P95_MS: "milliseconds",
            QualityMetricName.REQUESTS_PER_SECOND: "requests_per_second",
        }[self.name]

    def to_dict(self) -> dict[str, object]:
        return {
            "applicability": self.applicability.value,
            "name": self.name.value,
            "notes": self.notes,
            "sample_count": self.sample_count,
            "unit": self.unit,
            "value": self.value,
        }


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    RESTRICTED = "restricted"


class ConsentStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


@dataclass(frozen=True, slots=True)
class DatasetEvidence:
    dataset_id: str
    dataset_version: str
    manifest_sha256: str
    license_status: VerificationStatus
    license_identifier: str | None
    license_evidence_reference: str | None
    commercial_use_allowed: bool | None
    consent_status: ConsentStatus
    consent_evidence_reference: str | None
    territories: tuple[str, ...]

    def __post_init__(self) -> None:
        _required_text(self.dataset_id, "dataset_id")
        _required_text(self.dataset_version, "dataset_version")
        _sha256(self.manifest_sha256, "manifest_sha256")
        if not self.territories:
            raise ValueError("dataset evidence must declare at least one territory")
        if len(self.territories) != len(set(self.territories)):
            raise ValueError("dataset territories must be unique")
        if self.license_status is VerificationStatus.VERIFIED:
            if self.license_identifier is None or self.license_evidence_reference is None:
                raise ValueError("verified dataset license requires identifier and evidence")
            if self.commercial_use_allowed is None:
                raise ValueError("verified dataset license requires a commercial-use decision")
        if (
            self.consent_status is ConsentStatus.VERIFIED
            and self.consent_evidence_reference is None
        ):
            raise ValueError("verified dataset consent requires evidence")
        if (
            self.consent_status is ConsentStatus.NOT_REQUIRED
            and self.consent_evidence_reference is not None
        ):
            raise ValueError("consent evidence is invalid when consent is not required")

    @property
    def production_eligible(self) -> bool:
        return (
            self.license_status is VerificationStatus.VERIFIED
            and self.commercial_use_allowed is True
            and self.consent_status in {ConsentStatus.NOT_REQUIRED, ConsentStatus.VERIFIED}
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "commercial_use_allowed": self.commercial_use_allowed,
            "consent_evidence_reference": self.consent_evidence_reference,
            "consent_status": self.consent_status.value,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "license_evidence_reference": self.license_evidence_reference,
            "license_identifier": self.license_identifier,
            "license_status": self.license_status.value,
            "manifest_sha256": self.manifest_sha256,
            "production_eligible": self.production_eligible,
            "territories": list(self.territories),
        }


@dataclass(frozen=True, slots=True)
class EngineModelIdentity:
    engine_id: str
    engine_version: str
    model_id: str
    model_version: str
    weight_sha256: str

    def __post_init__(self) -> None:
        for field_name in ("engine_id", "engine_version", "model_id", "model_version"):
            _required_text(str(getattr(self, field_name)), field_name)
        _sha256(self.weight_sha256, "weight_sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "weight_sha256": self.weight_sha256,
        }


class RouteDecision(StrEnum):
    UNVERIFIED = "unverified"
    BLOCKED = "blocked"
    APPROVED = "approved"


@dataclass(frozen=True, slots=True)
class ModelBenchmarkEvidence:
    """Language-specific model route evidence; this type contains no implied results."""

    evidence_id: str
    task: ModelTask
    language: BenchmarkLanguage
    dataset: DatasetEvidence
    engine_model: EngineModelIdentity
    metrics: tuple[QualityMetric, ...]
    machine: MachineFingerprint | None = None
    decision: RouteDecision = RouteDecision.UNVERIFIED
    decision_reason: str = "Evidence has not completed production review"
    approved_by: str | None = None
    approved_at: datetime | None = None
    measured_at: datetime | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _required_text(self.evidence_id, "evidence_id")
        names = tuple(metric.name for metric in self.metrics)
        if len(names) != len(set(names)):
            raise ValueError("quality metric names must be unique")
        if set(names) != set(QualityMetricName):
            raise ValueError("evidence must declare applicability for every quality metric")
        if self.measured_at is not None:
            object.__setattr__(self, "measured_at", _utc(self.measured_at, "measured_at"))
        has_measurement = any(
            metric.applicability is MetricApplicability.APPLICABLE for metric in self.metrics
        )
        if has_measurement and self.measured_at is None:
            raise ValueError("measured metrics require measured_at")
        if has_measurement and self.machine is None:
            raise ValueError("measured metrics require a machine fingerprint")
        if not has_measurement and self.measured_at is not None:
            raise ValueError("measured_at is invalid when no metric was measured")
        if not has_measurement and self.machine is not None:
            raise ValueError("machine fingerprint is invalid when no metric was measured")
        _required_text(self.decision_reason, "decision_reason")
        if self.approved_at is not None:
            object.__setattr__(self, "approved_at", _utc(self.approved_at, "approved_at"))
        if self.decision is RouteDecision.APPROVED:
            if not self.dataset.production_eligible:
                raise ValueError("approved route requires production-eligible dataset rights")
            if not has_measurement:
                raise ValueError("approved route requires measured quality evidence")
            if any(
                metric.applicability is MetricApplicability.NOT_MEASURED for metric in self.metrics
            ):
                raise ValueError("approved route cannot contain an unmeasured quality metric")
            if self.approved_by is None or self.approved_at is None:
                raise ValueError("approved route requires approver and approval timestamp")
            if self.measured_at is not None and self.approved_at < self.measured_at:
                raise ValueError("route approval cannot precede measurement")
        elif self.approved_by is not None or self.approved_at is not None:
            raise ValueError("only an approved route may carry approval details")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported benchmark schema version: {self.schema_version}")

    @property
    def production_eligible(self) -> bool:
        return self.decision is RouteDecision.APPROVED

    def to_dict(self) -> dict[str, object]:
        return {
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "dataset": self.dataset.to_dict(),
            "decision": self.decision.value,
            "decision_reason": self.decision_reason,
            "engine_model": self.engine_model.to_dict(),
            "evidence_id": self.evidence_id,
            "language": self.language.value,
            "machine": self.machine.to_dict() if self.machine else None,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "production_eligible": self.production_eligible,
            "schema_version": self.schema_version,
            "task": self.task.value,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, sort_keys=True)


def unmeasured_quality_metrics(reason: str) -> tuple[QualityMetric, ...]:
    """Declare every metric unmeasured without manufacturing a numeric result."""

    _required_text(reason, "reason")
    return tuple(
        QualityMetric(
            name=name,
            applicability=MetricApplicability.NOT_MEASURED,
            notes=reason,
        )
        for name in QualityMetricName
    )


__all__ = [
    "SCHEMA_VERSION",
    "BenchmarkConfiguration",
    "BenchmarkLanguage",
    "BenchmarkReport",
    "BenchmarkResult",
    "BenchmarkSample",
    "ConsentStatus",
    "DatasetEvidence",
    "EngineModelIdentity",
    "MachineFingerprint",
    "MetricApplicability",
    "ModelBenchmarkEvidence",
    "ModelTask",
    "PerformanceThresholds",
    "QualityMetric",
    "QualityMetricName",
    "RouteDecision",
    "ThresholdFailure",
    "VerificationStatus",
    "unmeasured_quality_metrics",
]
