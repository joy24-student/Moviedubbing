"""Validated directed acyclic job graph."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable

from aidub.contracts.jobs import JobDescriptor


class JobGraph:
    """Immutable-in-spirit registry of jobs with deterministic ordering."""

    def __init__(self, jobs: Iterable[JobDescriptor] = ()) -> None:
        self._jobs: dict[str, JobDescriptor] = {}
        for job in jobs:
            self.add(job)
        self.validate()

    @property
    def jobs(self) -> tuple[JobDescriptor, ...]:
        return tuple(self._jobs[key] for key in sorted(self._jobs))

    def add(self, job: JobDescriptor) -> None:
        if job.job_id in self._jobs:
            raise ValueError(f"duplicate job id: {job.job_id}")
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> JobDescriptor:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(f"unknown job: {job_id}") from exc

    def validate(self) -> None:
        for job in self._jobs.values():
            missing = set(job.dependencies) - self._jobs.keys()
            if missing:
                names = ", ".join(sorted(missing))
                raise ValueError(f"job {job.job_id} has missing dependencies: {names}")
        self.topological_order()

    def topological_order(self) -> tuple[str, ...]:
        children: dict[str, list[str]] = defaultdict(list)
        indegree = dict.fromkeys(self._jobs, 0)
        for job in self._jobs.values():
            for dependency in job.dependencies:
                children[dependency].append(job.job_id)
                indegree[job.job_id] += 1

        ready = deque(sorted(key for key, degree in indegree.items() if degree == 0))
        result: list[str] = []
        while ready:
            node = ready.popleft()
            result.append(node)
            for child in sorted(children[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)

        if len(result) != len(self._jobs):
            cyclic = sorted(key for key, degree in indegree.items() if degree > 0)
            raise ValueError(f"job graph contains a cycle involving: {', '.join(cyclic)}")
        return tuple(result)

    def ready_jobs(
        self,
        *,
        completed: set[str],
        active: set[str] | None = None,
        failed: set[str] | None = None,
    ) -> tuple[JobDescriptor, ...]:
        active = active or set()
        failed = failed or set()
        ready: list[JobDescriptor] = []
        for job_id in self.topological_order():
            job = self._jobs[job_id]
            if job_id in completed or job_id in active or job_id in failed:
                continue
            if any(dependency in failed for dependency in job.dependencies):
                continue
            if set(job.dependencies) <= completed:
                ready.append(job)
        return tuple(ready)

    def descendants(self, job_id: str) -> frozenset[str]:
        self.get(job_id)
        direct: dict[str, set[str]] = defaultdict(set)
        for job in self._jobs.values():
            for dependency in job.dependencies:
                direct[dependency].add(job.job_id)
        found: set[str] = set()
        pending = list(direct[job_id])
        while pending:
            child = pending.pop()
            if child not in found:
                found.add(child)
                pending.extend(direct[child])
        return frozenset(found)
