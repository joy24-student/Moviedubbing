"""Cross-process advisory project locks with auditable orphan recovery.

The stable ``.aidub.lock`` file carries the operating-system lock. A separate
``.aidub.lock.json`` record is published atomically, because replacing a locked
file would change its inode/handle and invalidate the advisory-lock protocol.
"""

from __future__ import annotations

import errno
import importlib
import json
import os
import re
import secrets
import socket
import stat
import tempfile
import threading
from collections.abc import Callable
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Protocol, Self, cast

from .errors import (
    ActiveLockCannotBeBrokenError,
    InvalidLockRecordError,
    LockContendedError,
    LockNonceMismatchError,
    LockRecordNotFoundError,
    OrphanedLockRecordError,
    UnsafeLockPathError,
)
from .models import LockBreakEvent, LockInspection, LockRecord, LockState

BreakAuditCallback = Callable[[LockBreakEvent], None]

_FORMAT_VERSION = 1
_NONCE = re.compile(r"^[0-9a-f]{32}$")
_MAX_RECORD_BYTES = 16 * 1024
_PROCESS_OWNERS: dict[str, str] = {}
_PROCESS_OWNERS_GUARD = threading.Lock()
_RESERVATION_PREFIX = "reservation:"


class _OsLockApi(Protocol):
    def acquire(self, descriptor: int) -> None: ...

    def release(self, descriptor: int) -> None: ...


class _WindowsLockApi:
    def __init__(self) -> None:
        api = vars(importlib.import_module("msvcrt"))
        self._locking = cast("Callable[[int, int, int], None]", api["locking"])
        self._acquire_mode = cast("int", api["LK_NBLCK"])
        self._release_mode = cast("int", api["LK_UNLCK"])

    def acquire(self, descriptor: int) -> None:
        self._locking(descriptor, self._acquire_mode, 1)

    def release(self, descriptor: int) -> None:
        self._locking(descriptor, self._release_mode, 1)


class _PosixLockApi:
    def __init__(self) -> None:
        api = vars(importlib.import_module("fcntl"))
        self._flock = cast("Callable[[int, int], None]", api["flock"])
        self._acquire_mode = cast("int", api["LOCK_EX"]) | cast("int", api["LOCK_NB"])
        self._release_mode = cast("int", api["LOCK_UN"])

    def acquire(self, descriptor: int) -> None:
        self._flock(descriptor, self._acquire_mode)

    def release(self, descriptor: int) -> None:
        self._flock(descriptor, self._release_mode)


_OS_LOCK: _OsLockApi = _WindowsLockApi() if os.name == "nt" else _PosixLockApi()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _is_link_or_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(info, "st_file_attributes", 0) & reparse_flag)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        if os.name == "nt":
            return
        raise
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _parse_utc_timestamp(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidLockRecordError("lock started_at must be a UTC RFC 3339 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise InvalidLockRecordError("lock started_at is not an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise InvalidLockRecordError("lock started_at must use UTC")
    return value


def _record_from_payload(payload: object) -> LockRecord:
    if not isinstance(payload, dict):
        raise InvalidLockRecordError("lock record must be a JSON object")
    expected_fields = {"format_version", "process_id", "hostname", "started_at", "nonce"}
    if set(payload) != expected_fields:
        raise InvalidLockRecordError("lock record fields do not match format version 1")
    version = payload["format_version"]
    process_id = payload["process_id"]
    hostname = payload["hostname"]
    nonce = payload["nonce"]
    if type(version) is not int or version != _FORMAT_VERSION:
        raise InvalidLockRecordError(f"unsupported lock record version: {version!r}")
    if type(process_id) is not int or process_id <= 0:
        raise InvalidLockRecordError("lock process_id must be a positive integer")
    if not isinstance(hostname, str) or not hostname.strip() or len(hostname) > 255:
        raise InvalidLockRecordError("lock hostname must be a non-empty string")
    if not isinstance(nonce, str) or _NONCE.fullmatch(nonce) is None:
        raise InvalidLockRecordError("lock nonce must contain 32 lowercase hexadecimal characters")
    return LockRecord(
        format_version=version,
        process_id=process_id,
        hostname=hostname,
        started_at=_parse_utc_timestamp(payload["started_at"]),
        nonce=nonce,
    )


def _record_payload(record: LockRecord) -> bytes:
    return (
        json.dumps(
            {
                "format_version": record.format_version,
                "hostname": record.hostname,
                "nonce": record.nonce,
                "process_id": record.process_id,
                "started_at": record.started_at,
            },
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


class ProjectLock:
    """Exclusive advisory lock for one existing project directory."""

    def __init__(self, project_path: Path | str) -> None:
        candidate = Path(project_path).expanduser()
        if not candidate.is_absolute():
            raise UnsafeLockPathError("project lock path must be absolute")
        if candidate.suffix.casefold() != ".aidub":
            raise UnsafeLockPathError("project lock path must identify a .aidub directory")
        if _is_link_or_reparse(candidate):
            raise UnsafeLockPathError(f"project path cannot be a link/reparse point: {candidate}")
        if not candidate.is_dir():
            raise UnsafeLockPathError(f"project path is not an existing directory: {candidate}")
        self.project_path = candidate.resolve()
        self.lock_path = self.project_path / ".aidub.lock"
        self.record_path = self.project_path / ".aidub.lock.json"
        self._key = os.path.normcase(str(self.lock_path))
        self._stream: IO[bytes] | None = None
        self._record: LockRecord | None = None

    @property
    def held(self) -> bool:
        return self._stream is not None

    @property
    def record(self) -> LockRecord | None:
        return self._record

    def _validate_managed_paths(self) -> None:
        if _is_link_or_reparse(self.project_path) or not self.project_path.is_dir():
            raise UnsafeLockPathError(f"project directory became unsafe: {self.project_path}")
        for path in (self.lock_path, self.record_path):
            if _is_link_or_reparse(path):
                raise UnsafeLockPathError(f"lock protocol file cannot be a link: {path}")
            if path.exists() and not path.is_file():
                raise UnsafeLockPathError(f"lock protocol path is not a regular file: {path}")

    def _open_gate(self) -> IO[bytes]:
        self._validate_managed_paths()
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(self.lock_path, flags, 0o600)
        try:
            info = os.fstat(descriptor)
            self._assert_regular_gate(info)
            if info.st_size == 0:
                os.write(descriptor, b"\0")
                os.fsync(descriptor)
            os.lseek(descriptor, 0, os.SEEK_SET)
            return os.fdopen(descriptor, "r+b", buffering=0)
        except BaseException:
            os.close(descriptor)
            raise

    def _assert_regular_gate(self, info: os.stat_result) -> None:
        if not stat.S_ISREG(info.st_mode):
            raise UnsafeLockPathError(f"lock gate is not a regular file: {self.lock_path}")

    @staticmethod
    def _try_os_lock(stream: IO[bytes]) -> bool:
        descriptor = stream.fileno()
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            _OS_LOCK.acquire(descriptor)
        except OSError as exc:
            if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                return False
            raise
        return True

    @staticmethod
    def _unlock_os(stream: IO[bytes]) -> None:
        descriptor = stream.fileno()
        os.lseek(descriptor, 0, os.SEEK_SET)
        _OS_LOCK.release(descriptor)

    def _read_record(self, *, missing_ok: bool) -> LockRecord | None:
        self._validate_managed_paths()
        try:
            info = self.record_path.lstat()
        except FileNotFoundError:
            if missing_ok:
                return None
            raise LockRecordNotFoundError(
                f"project has no lock record: {self.record_path}"
            ) from None
        if not stat.S_ISREG(info.st_mode) or _is_link_or_reparse(self.record_path):
            raise InvalidLockRecordError(f"lock record is not a regular file: {self.record_path}")
        if info.st_size > _MAX_RECORD_BYTES:
            raise InvalidLockRecordError("lock record exceeds the maximum safe size")
        try:
            raw = self.record_path.read_bytes()
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidLockRecordError(f"cannot parse lock record: {exc}") from exc
        return _record_from_payload(payload)

    def _write_record_atomic(self, record: LockRecord) -> None:
        self._validate_managed_paths()
        descriptor, raw_path = tempfile.mkstemp(
            prefix=".aidub.lock.", suffix=".tmp", dir=self.project_path
        )
        temporary = Path(raw_path)
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(_record_payload(record))
                stream.flush()
                os.fsync(stream.fileno())
            self._validate_managed_paths()
            temporary.replace(self.record_path)
            _fsync_directory(self.project_path)
        finally:
            temporary.unlink(missing_ok=True)

    def _reserve_process(self, owner: str) -> bool:
        with _PROCESS_OWNERS_GUARD:
            if self._key in _PROCESS_OWNERS:
                return False
            _PROCESS_OWNERS[self._key] = owner
            return True

    def _unreserve_process(self, owner: str) -> None:
        with _PROCESS_OWNERS_GUARD:
            if _PROCESS_OWNERS.get(self._key) == owner:
                del _PROCESS_OWNERS[self._key]

    def acquire(self) -> LockRecord:
        """Acquire without waiting; orphan records require explicit break first."""

        if self._record is not None:
            return self._record
        nonce = secrets.token_hex(16)
        if not self._reserve_process(nonce):
            record = self._read_record(missing_ok=True)
            raise LockContendedError(
                "this process already owns or is inspecting the project lock", record=record
            )
        with ExitStack() as cleanup:
            cleanup.callback(self._unreserve_process, nonce)
            stream = self._open_gate()
            cleanup.callback(stream.close)
            if not self._try_os_lock(stream):
                self._raise_active_contention()
            cleanup.callback(self._unlock_os, stream)
            existing = self._read_record(missing_ok=True)
            if existing is not None:
                self._raise_orphaned(existing)
            record = LockRecord(
                process_id=os.getpid(),
                hostname=socket.gethostname(),
                started_at=_utc_now(),
                nonce=nonce,
            )
            self._write_record_atomic(record)
            self._stream = stream
            self._record = record
            cleanup.pop_all()
        return record

    def _raise_active_contention(self) -> None:
        record = self._read_record(missing_ok=True)
        raise LockContendedError("project is locked by another process", record=record)

    @staticmethod
    def _raise_orphaned(record: LockRecord) -> None:
        raise OrphanedLockRecordError(record)

    def try_acquire(self) -> LockRecord | None:
        """Return ``None`` only for active contention; safety failures still raise."""

        try:
            return self.acquire()
        except LockContendedError:
            return None

    def release(self) -> None:
        """Release ownership. Calling release repeatedly is safe."""

        stream = self._stream
        record = self._record
        if stream is None or record is None:
            return
        ownership_error: LockNonceMismatchError | None = None
        operation_error: OSError | None = None
        try:
            current = self._read_record(missing_ok=True)
            if current is None or current.nonce != record.nonce:
                ownership_error = LockNonceMismatchError(
                    "lock record no longer matches this owner's nonce; it was not removed"
                )
            else:
                try:
                    self.record_path.unlink()
                    _fsync_directory(self.project_path)
                except OSError as exc:
                    operation_error = exc
        finally:
            try:
                self._unlock_os(stream)
            finally:
                stream.close()
                self._stream = None
                self._record = None
                self._unreserve_process(record.nonce)
        if operation_error is not None:
            raise operation_error
        if ownership_error is not None:
            raise ownership_error

    def inspect(self) -> LockInspection:
        """Return a race-prone diagnostic snapshot; never infer safety from PID/age."""

        try:
            record = self._read_record(missing_ok=True)
        except (InvalidLockRecordError, UnsafeLockPathError) as exc:
            return LockInspection(
                state=LockState.INVALID,
                lock_path=self.lock_path,
                record_path=self.record_path,
                detail=str(exc),
            )
        with _PROCESS_OWNERS_GUARD:
            locally_held = self._key in _PROCESS_OWNERS
        if locally_held:
            return LockInspection(
                state=LockState.HELD,
                lock_path=self.lock_path,
                record_path=self.record_path,
                record=record,
            )
        reservation = f"{_RESERVATION_PREFIX}{secrets.token_hex(16)}"
        if not self._reserve_process(reservation):
            return LockInspection(
                state=LockState.HELD,
                lock_path=self.lock_path,
                record_path=self.record_path,
                record=record,
            )
        stream: IO[bytes] | None = None
        acquired = False
        try:
            stream = self._open_gate()
            acquired = self._try_os_lock(stream)
            if not acquired:
                return LockInspection(
                    state=LockState.HELD,
                    lock_path=self.lock_path,
                    record_path=self.record_path,
                    record=record,
                )
            state = LockState.ORPHANED if record is not None else LockState.UNLOCKED
            return LockInspection(
                state=state,
                lock_path=self.lock_path,
                record_path=self.record_path,
                record=record,
            )
        finally:
            if stream is not None:
                if acquired:
                    self._unlock_os(stream)
                stream.close()
            self._unreserve_process(reservation)

    def break_lock(
        self,
        *,
        expected_nonce: str,
        reason: str,
        audit_callback: BreakAuditCallback,
    ) -> LockBreakEvent:
        """Remove an orphan record only after nonce match and durable audit hook.

        An operating-system lock is never stolen. If a compliant owner remains
        active this method fails, regardless of PID existence or record age.
        """

        if _NONCE.fullmatch(expected_nonce) is None:
            raise ValueError("expected_nonce must contain 32 lowercase hexadecimal characters")
        if not reason.strip():
            raise ValueError("lock-break reason must not be empty")
        reservation = f"{_RESERVATION_PREFIX}{secrets.token_hex(16)}"
        if not self._reserve_process(reservation):
            raise ActiveLockCannotBeBrokenError("project lock is active in this process")
        stream: IO[bytes] | None = None
        acquired = False
        try:
            stream = self._open_gate()
            acquired = self._try_os_lock(stream)
            if not acquired:
                raise ActiveLockCannotBeBrokenError(
                    "operating-system project lock is active; it cannot be stolen"
                )
            record = self._read_record(missing_ok=False)
            assert record is not None
            if record.nonce != expected_nonce:
                raise LockNonceMismatchError(
                    f"lock nonce changed; expected {expected_nonce}, observed {record.nonce}"
                )
            event = LockBreakEvent(
                project_path=self.project_path,
                record=record,
                broken_at=_utc_now(),
                breaker_process_id=os.getpid(),
                breaker_hostname=socket.gethostname(),
                reason=reason.strip(),
            )
            # The callback must durably record/emit the event. Failure aborts the break.
            audit_callback(event)
            current = self._read_record(missing_ok=False)
            assert current is not None
            if current.nonce != expected_nonce:
                raise LockNonceMismatchError("lock record changed during guarded break")
            self.record_path.unlink()
            _fsync_directory(self.project_path)
            return event
        finally:
            if stream is not None:
                if acquired:
                    self._unlock_os(stream)
                stream.close()
            self._unreserve_process(reservation)

    def __enter__(self) -> Self:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.release()


__all__ = ["BreakAuditCallback", "ProjectLock"]
