"""Deterministic Phase 0 control-plane benchmark workloads."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Final

from aidub.contracts.jobs import JobDescriptor
from aidub.domain.time import RationalRate, TickRescaler
from aidub.orchestration.graph import JobGraph

from .models import BenchmarkConfiguration, PerformanceThresholds

RATIONAL_TIME_WORKLOAD: Final = "rational_time_operations"
JOB_DAG_WORKLOAD: Final = "job_dag_construction_traversal"

# These are explicit engineering tripwires, not measured product baselines. Promotion or tightening
# follows the review process in docs/quality/benchmark-protocol.md.
RATIONAL_TIME_PROVISIONAL_THRESHOLDS: Final = PerformanceThresholds(
    max_median_ms=5_000.0,
    max_p95_ms=7_500.0,
    min_throughput_items_per_second=10_000.0,
    provisional=True,
    rationale=(
        "Phase 0 guardrail for 100,000 exact frame/sample operations on the Pro reference tier"
    ),
)
JOB_DAG_PROVISIONAL_THRESHOLDS: Final = PerformanceThresholds(
    max_median_ms=7_500.0,
    max_p95_ms=10_000.0,
    min_throughput_items_per_second=500.0,
    provisional=True,
    rationale="Phase 0 guardrail for deterministic job DAG construction and traversal",
)

_NTSC_RATE: Final = RationalRate(numerator=24_000, denominator=1_001)
_AUDIO_RATE: Final = RationalRate(numerator=48_000)
_FIXED_CREATED_AT: Final = datetime(2026, 1, 1, tzinfo=UTC)


def rational_time_operations(item_count: int) -> int:
    """Exercise the production bulk transform used by accelerated editor paths."""

    if item_count < 1:
        raise ValueError("item_count must be positive")
    frames_to_samples = TickRescaler(_NTSC_RATE, _AUDIO_RATE)
    samples_to_frames = TickRescaler(_AUDIO_RATE, _NTSC_RATE)
    checksum = 0
    for index in range(item_count):
        audio_ticks = frames_to_samples.rescale_ticks(index)
        round_trip_ticks = samples_to_frames.rescale_ticks(audio_ticks)
        if round_trip_ticks != index:
            raise AssertionError("exact rational-time round trip changed the frame position")
        # Half-open bulk ranges use validated integer clocks at the boundary.
        if index + 1 <= index:
            raise AssertionError("time range end invariant failed")
        checksum ^= audio_ticks
    # Consume deterministic state so future workload refactors cannot remove all computed values.
    if checksum < 0:
        raise AssertionError("unreachable rational-time checksum")
    return item_count


def build_job_dag(item_count: int) -> JobGraph:
    """Build a deterministic binary-tree DAG using production contract and graph types."""

    if item_count < 1:
        raise ValueError("item_count must be positive")
    jobs: list[JobDescriptor] = []
    for index in range(item_count):
        job_id = f"bench-job-{index:08d}"
        dependencies = () if index == 0 else (f"bench-job-{(index - 1) // 2:08d}",)
        jobs.append(
            JobDescriptor(
                job_id=job_id,
                idempotency_key=hashlib.sha256(job_id.encode("ascii")).hexdigest(),
                project_id="bench-project",
                job_type="benchmark.dag",
                dependencies=dependencies,
                created_at=_FIXED_CREATED_AT,
            )
        )
    return JobGraph(jobs)


def job_dag_construction_traversal(item_count: int) -> int:
    """Construct, topologically traverse, query readiness, and walk descendants."""

    graph = build_job_dag(item_count)
    order = graph.topological_order()
    descendants = graph.descendants("bench-job-00000000")
    ready = graph.ready_jobs(completed=set())
    if len(order) != item_count or len(descendants) != item_count - 1:
        raise AssertionError("job DAG traversal did not visit every node")
    if len(ready) != 1 or ready[0].job_id != "bench-job-00000000":
        raise AssertionError("job DAG readiness invariant failed")
    return item_count


def rational_time_configuration(
    *,
    item_count: int = 100_000,
    warmups: int = 2,
    repetitions: int = 7,
) -> BenchmarkConfiguration:
    return BenchmarkConfiguration(
        workload_name=RATIONAL_TIME_WORKLOAD,
        item_count=item_count,
        warmups=warmups,
        repetitions=repetitions,
        thresholds=RATIONAL_TIME_PROVISIONAL_THRESHOLDS,
    )


def job_dag_configuration(
    *,
    item_count: int = 10_000,
    warmups: int = 1,
    repetitions: int = 5,
) -> BenchmarkConfiguration:
    return BenchmarkConfiguration(
        workload_name=JOB_DAG_WORKLOAD,
        item_count=item_count,
        warmups=warmups,
        repetitions=repetitions,
        thresholds=JOB_DAG_PROVISIONAL_THRESHOLDS,
    )


__all__ = [
    "JOB_DAG_PROVISIONAL_THRESHOLDS",
    "JOB_DAG_WORKLOAD",
    "RATIONAL_TIME_PROVISIONAL_THRESHOLDS",
    "RATIONAL_TIME_WORKLOAD",
    "build_job_dag",
    "job_dag_configuration",
    "job_dag_construction_traversal",
    "rational_time_configuration",
    "rational_time_operations",
]
