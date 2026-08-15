"""Lifecycle management for an isolated spawned worker."""

from __future__ import annotations

import multiprocessing as mp
import queue
import time
from dataclasses import dataclass
from multiprocessing.process import BaseProcess
from typing import Any, Self, cast

from aidub.contracts.jobs import JobDescriptor, JobProgress, JobResult

from .process import worker_process_main


class WorkerTimeoutError(TimeoutError):
    pass


class WorkerCrashedError(RuntimeError):
    def __init__(self, exit_code: int | None) -> None:
        super().__init__(f"worker process exited unexpectedly with code {exit_code}")
        self.exit_code = exit_code


@dataclass(frozen=True, slots=True)
class WorkerEvent:
    event_type: str
    job_id: str | None = None
    progress: JobProgress | None = None
    diagnostic: str | None = None


class LocalWorkerSupervisor:
    """Owns one spawned process and serializes jobs through it.

    Dedicated engine pools will compose this primitive. Starting with a
    single-worker primitive keeps lifecycle and crash semantics testable.
    """

    def __init__(self, *, startup_timeout_seconds: float = 10.0) -> None:
        self._ctx = mp.get_context("spawn")
        self._job_queue: Any | None = None
        self._control_queue: Any | None = None
        self._result_queue: Any | None = None
        self._process: BaseProcess | None = None
        self._active_job_id: str | None = None
        self._startup_timeout_seconds = startup_timeout_seconds

    @property
    def is_alive(self) -> bool:
        return self._process is not None and self._process.is_alive()

    @property
    def process_id(self) -> int | None:
        return self._process.pid if self._process is not None else None

    def start(self) -> None:
        if self.is_alive:
            return
        self._job_queue = self._ctx.Queue()
        self._control_queue = self._ctx.Queue()
        self._result_queue = self._ctx.Queue()
        self._process = self._ctx.Process(
            target=worker_process_main,
            args=(self._job_queue, self._control_queue, self._result_queue),
            name="aidub-local-worker",
            daemon=True,
        )
        process = self._process
        process.start()
        message = self._receive(self._startup_timeout_seconds)
        assert message is not None
        if message.get("type") != "ready":
            self.terminate()
            raise RuntimeError("worker did not complete its startup handshake")

    def restart(self) -> None:
        self.terminate()
        self.start()

    def submit(self, job: JobDescriptor) -> None:
        self._ensure_alive()
        if self._active_job_id is not None:
            raise RuntimeError(f"worker already has active job {self._active_job_id}")
        assert self._job_queue is not None
        self._active_job_id = job.job_id
        self._job_queue.put({"type": "job", "payload": job.model_dump(mode="json")})

    def cancel(self, job_id: str) -> None:
        self._ensure_alive()
        if job_id != self._active_job_id:
            raise ValueError(f"job {job_id} is not active")
        assert self._control_queue is not None
        self._control_queue.put({"type": "cancel", "job_id": job_id})

    def wait(
        self,
        *,
        timeout_seconds: float = 30.0,
        on_event: Any | None = None,
    ) -> JobResult:
        if self._active_job_id is None:
            raise RuntimeError("no active job")
        deadline = time.monotonic() + timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise WorkerTimeoutError(f"job {self._active_job_id} exceeded wait timeout")
            message = self._receive(min(remaining, 0.25), allow_empty=True)
            if message is None:
                self._ensure_alive()
                continue
            message_type = message.get("type")
            if message_type == "progress":
                progress = JobProgress.model_validate(message["payload"])
                if on_event is not None:
                    on_event(
                        WorkerEvent(
                            event_type="progress",
                            job_id=progress.job_id,
                            progress=progress,
                        )
                    )
            elif message_type == "diagnostic" and on_event is not None:
                on_event(
                    WorkerEvent(
                        event_type="diagnostic",
                        job_id=message.get("job_id"),
                        diagnostic=message.get("traceback"),
                    )
                )
            elif message_type == "result":
                result = JobResult.model_validate(message["payload"])
                if result.job_id != self._active_job_id:
                    raise RuntimeError("worker returned a result for the wrong job")
                self._active_job_id = None
                return result

    def shutdown(self, *, timeout_seconds: float = 5.0) -> None:
        if self._process is None:
            return
        if self._process.is_alive() and self._job_queue is not None:
            self._job_queue.put({"type": "shutdown"})
            self._process.join(timeout_seconds)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout_seconds)
        self._close_queues()
        self._process = None
        self._active_job_id = None

    def terminate(self) -> None:
        if self._process is not None and self._process.is_alive():
            self._process.terminate()
            self._process.join(5)
        self._close_queues()
        self._process = None
        self._active_job_id = None

    def _receive(
        self, timeout_seconds: float, *, allow_empty: bool = False
    ) -> dict[str, Any] | None:
        assert self._result_queue is not None
        try:
            return cast("dict[str, Any]", self._result_queue.get(timeout=timeout_seconds))
        except queue.Empty:
            if allow_empty:
                return None
            self._ensure_alive()
            raise WorkerTimeoutError("timed out waiting for worker") from None

    def _ensure_alive(self) -> None:
        if self._process is None:
            raise RuntimeError("worker has not been started")
        if not self._process.is_alive():
            exit_code = self._process.exitcode
            self._active_job_id = None
            raise WorkerCrashedError(exit_code)

    def _close_queues(self) -> None:
        for item in (self._job_queue, self._control_queue, self._result_queue):
            if item is not None:
                item.close()
                item.join_thread()
        self._job_queue = None
        self._control_queue = None
        self._result_queue = None

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.shutdown()
