"""Orchestration compatibility wrapper around the canonical domain lifecycle."""

from __future__ import annotations

from dataclasses import dataclass

from aidub.domain.job import JobStatus, can_transition_job_status

# Preserve the original orchestration import surface while keeping one source of truth.
JobState = JobStatus
TERMINAL_STATES = frozenset({JobStatus.CANCELLED, JobStatus.FAILED, JobStatus.SUCCEEDED})


class TransitionError(ValueError):
    """Raised when the canonical job lifecycle rejects a requested change."""


@dataclass(slots=True)
class JobStateMachine:
    """Small mutable façade for orchestration code over immutable domain states."""

    state: JobStatus = JobStatus.QUEUED

    def can_transition_to(self, target: JobStatus) -> bool:
        return can_transition_job_status(self.state, target)

    def transition_to(self, target: JobStatus) -> JobStatus:
        if not self.can_transition_to(target):
            raise TransitionError(f"invalid job transition: {self.state.value} -> {target.value}")
        self.state = target
        return self.state


__all__ = ["TERMINAL_STATES", "JobState", "JobStateMachine", "TransitionError"]
