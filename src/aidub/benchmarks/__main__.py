"""Run Phase 0 control-plane benchmarks with ``python -m aidub.benchmarks``."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from .models import BenchmarkReport, MachineFingerprint
from .runner import BenchmarkRunner
from .workloads import (
    job_dag_configuration,
    job_dag_construction_traversal,
    rational_time_configuration,
    rational_time_operations,
)

_WORKLOAD_CHOICES: Final = ("all", "rational-time", "job-dag")


def _positive(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _non_negative(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value cannot be negative")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic AI Dubbing Studio benchmarks")
    parser.add_argument("--workload", choices=_WORKLOAD_CHOICES, default="all")
    parser.add_argument("--rational-items", type=_positive, default=100_000)
    parser.add_argument("--dag-items", type=_positive, default=10_000)
    parser.add_argument("--warmups", type=_non_negative, default=1)
    parser.add_argument("--repetitions", type=_positive, default=5)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    machine = MachineFingerprint.capture()
    runner = BenchmarkRunner()
    results = []
    if args.workload in {"all", "rational-time"}:
        results.append(
            runner.run(
                rational_time_configuration(
                    item_count=args.rational_items,
                    warmups=args.warmups,
                    repetitions=args.repetitions,
                ),
                rational_time_operations,
                machine=machine,
            )
        )
    if args.workload in {"all", "job-dag"}:
        results.append(
            runner.run(
                job_dag_configuration(
                    item_count=args.dag_items,
                    warmups=args.warmups,
                    repetitions=args.repetitions,
                ),
                job_dag_construction_traversal,
                machine=machine,
            )
        )
    report = BenchmarkReport(
        generated_at=datetime.now(UTC),
        machine=machine,
        results=tuple(results),
    )
    payload = f"{report.to_json()}\n"
    if args.output is None:
        sys.stdout.write(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
