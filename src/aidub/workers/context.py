"""Cooperative cancellation and progress context inside a worker."""

from __future__ import annotations

import queue
from dataclasses import dataclass
from typing import Any

from aidub.contracts.jobs import JobProgress


class JobCancelledError(RuntimeError):
    pass


@dataclass(slots=True)
class WorkerContext:
    job_id: str
    _control_queue: Any
    _result_queue: Any
    _cancelled: bool = False

    def _poll_controls(self) -> None:
        while True:
            try:
                message = self._control_queue.get_nowait()
            except queue.Empty:
                return
            if message.get("type") == "cancel" and message.get("job_id") == self.job_id:
                self._cancelled = True

    def is_cancelled(self) -> bool:
        self._poll_controls()
        return self._cancelled

    def checkpoint(self) -> None:
        if self.is_cancelled():
            raise JobCancelledError(f"job {self.job_id} was cancelled")

    def progress(self, progress: JobProgress) -> None:
        if progress.job_id != self.job_id:
            raise ValueError("progress job_id does not match active job")
        self._result_queue.put({"type": "progress", "payload": progress.model_dump(mode="json")})
