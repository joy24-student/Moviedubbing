"""Injectable benchmark execution and deterministic statistics."""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from .models import (
    BenchmarkConfiguration,
    BenchmarkResult,
    BenchmarkSample,
    MachineFingerprint,
    ThresholdFailure,
)


class BenchmarkWorkload(Protocol):
    """Execute exactly ``item_count`` logical operations and report the completed count."""

    def __call__(self, item_count: int) -> int: ...


class NanosecondClock(Protocol):
    def __call__(self) -> int: ...


class BenchmarkExecutionError(RuntimeError):
    """Raised when timing or workload accounting cannot yield valid evidence."""


def _run_id() -> str:
    return f"bench_{uuid4().hex}"


def _now() -> datetime:
    return datetime.now(UTC)


def nearest_rank_percentile(values: tuple[int, ...], percentile: float) -> int:
    """Return the nearest-rank percentile for positive integer measurements."""

    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0 < percentile <= 1:
        raise ValueError("percentile must be in the interval (0, 1]")
    ordered = sorted(values)
    rank = math.ceil(percentile * len(ordered))
    return ordered[rank - 1]


class BenchmarkRunner:
    """Run warmups and measured repetitions using injectable process boundaries."""

    def __init__(
        self,
        *,
        clock: NanosecondClock = time.perf_counter_ns,
        now: Callable[[], datetime] = _now,
        run_id_factory: Callable[[], str] = _run_id,
    ) -> None:
        self._clock = clock
        self._now = now
        self._run_id_factory = run_id_factory

    def run(
        self,
        configuration: BenchmarkConfiguration,
        workload: BenchmarkWorkload,
        *,
        machine: MachineFingerprint | None = None,
    ) -> BenchmarkResult:
        """Execute one workload and evaluate its measured statistics against all gates."""

        started_at = self._now()
        for _ in range(configuration.warmups):
            self._execute_once(configuration, workload)

        samples: list[BenchmarkSample] = []
        for repetition in range(1, configuration.repetitions + 1):
            before = self._clock()
            completed = self._execute_once(configuration, workload)
            after = self._clock()
            elapsed_ns = after - before
            if elapsed_ns <= 0:
                raise BenchmarkExecutionError("benchmark clock did not advance monotonically")
            throughput = completed * 1_000_000_000 / elapsed_ns
            samples.append(
                BenchmarkSample(
                    repetition=repetition,
                    elapsed_ns=elapsed_ns,
                    completed_items=completed,
                    throughput_items_per_second=throughput,
                )
            )

        elapsed_values = tuple(sample.elapsed_ns for sample in samples)
        median_ms = float(statistics.median(elapsed_values)) / 1_000_000
        p95_ms = nearest_rank_percentile(elapsed_values, 0.95) / 1_000_000
        total_items = sum(sample.completed_items for sample in samples)
        total_elapsed_ns = sum(elapsed_values)
        throughput = total_items * 1_000_000_000 / total_elapsed_ns
        failures = self._evaluate_thresholds(
            configuration,
            median_ms=median_ms,
            p95_ms=p95_ms,
            throughput_items_per_second=throughput,
        )
        return BenchmarkResult(
            run_id=self._run_id_factory(),
            started_at=started_at,
            finished_at=self._now(),
            machine=machine or MachineFingerprint.capture(),
            configuration=configuration,
            samples=tuple(samples),
            median_ms=median_ms,
            p95_ms=p95_ms,
            throughput_items_per_second=throughput,
            threshold_failures=failures,
        )

    @staticmethod
    def _execute_once(
        configuration: BenchmarkConfiguration,
        workload: BenchmarkWorkload,
    ) -> int:
        completed = workload(configuration.item_count)
        if isinstance(completed, bool) or not isinstance(completed, int):
            raise BenchmarkExecutionError("benchmark workload must return an integer item count")
        if completed != configuration.item_count:
            raise BenchmarkExecutionError(
                "benchmark workload completed "
                f"{completed} items; expected {configuration.item_count}"
            )
        return completed

    @staticmethod
    def _evaluate_thresholds(
        configuration: BenchmarkConfiguration,
        *,
        median_ms: float,
        p95_ms: float,
        throughput_items_per_second: float,
    ) -> tuple[ThresholdFailure, ...]:
        thresholds = configuration.thresholds
        failures: list[ThresholdFailure] = []
        if thresholds.max_median_ms is not None and median_ms > thresholds.max_median_ms:
            failures.append(
                ThresholdFailure(
                    metric="median_ms",
                    observed=median_ms,
                    comparator="<=",
                    threshold=thresholds.max_median_ms,
                )
            )
        if thresholds.max_p95_ms is not None and p95_ms > thresholds.max_p95_ms:
            failures.append(
                ThresholdFailure(
                    metric="p95_ms",
                    observed=p95_ms,
                    comparator="<=",
                    threshold=thresholds.max_p95_ms,
                )
            )
        minimum_throughput = thresholds.min_throughput_items_per_second
        if minimum_throughput is not None and throughput_items_per_second < minimum_throughput:
            failures.append(
                ThresholdFailure(
                    metric="throughput_items_per_second",
                    observed=throughput_items_per_second,
                    comparator=">=",
                    threshold=minimum_throughput,
                )
            )
        return tuple(failures)


__all__ = [
    "BenchmarkExecutionError",
    "BenchmarkRunner",
    "BenchmarkWorkload",
    "NanosecondClock",
    "nearest_rank_percentile",
]
