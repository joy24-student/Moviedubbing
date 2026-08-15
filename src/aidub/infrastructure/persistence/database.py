"""SQLite-backed local project database.

Every write goes through :meth:`ProjectDatabase.transaction`, which combines a
process-local single-writer lock with SQLite ``BEGIN IMMEDIATE`` serialization.
Transactions are deliberately short; callers must not run media or AI work while
holding one.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aidub.domain import JobStatus as DomainJobStatus
from aidub.domain import can_transition_job_status

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

from .errors import (
    DatabaseNotInitializedError,
    IntegrityCheckError,
    InvalidStateTransitionError,
    PersistenceError,
)
from .migrations import (
    apply_migrations,
    current_schema_version,
    discover_migrations,
    read_migration_history,
)
from .models import (
    ArtifactRecord,
    ArtifactStatus,
    AuditEventRecord,
    IntegrityReport,
    JobRecord,
    JobState,
    MigrationInfo,
    MigrationReport,
    ProjectRecord,
    ReproducibilityLevel,
    utc_now,
)

_WRITER_LOCKS: dict[str, threading.RLock] = {}
_WRITER_LOCKS_GUARD = threading.Lock()
_WRITER_CONTEXT = threading.local()


def _canonical_json(value: Mapping[str, Any] | None) -> str:
    return json.dumps(
        {} if value is None else value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _load_json(value: str | None) -> dict[str, Any]:
    if value is None:
        return {}
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        raise PersistenceError("database JSON object column contains a non-object value")
    return decoded


def _writer_lock(path: Path) -> threading.RLock:
    key = os.path.normcase(str(path.resolve()))
    with _WRITER_LOCKS_GUARD:
        return _WRITER_LOCKS.setdefault(key, threading.RLock())


class ProjectDatabase:
    """Own a single local ``project.db`` and its migration lifecycle."""

    def __init__(
        self,
        path: Path | str,
        *,
        migrations_directory: Path | str | None = None,
        busy_timeout_ms: int = 15_000,
    ) -> None:
        self.path = Path(path).expanduser().resolve()
        self.migrations_directory = (
            Path(migrations_directory).expanduser().resolve()
            if migrations_directory is not None
            else None
        )
        if busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must not be negative")
        self.busy_timeout_ms = busy_timeout_ms
        self._writer_lock = _writer_lock(self.path)

    @property
    def supported_schema_version(self) -> int:
        return discover_migrations(self.migrations_directory)[-1].version

    def _open_connection(self, *, read_only: bool) -> sqlite3.Connection:
        if read_only:
            if not self.path.is_file():
                raise DatabaseNotInitializedError(f"project database does not exist: {self.path}")
            database = f"{self.path.as_uri()}?mode=ro"
            connection = sqlite3.connect(
                database,
                uri=True,
                isolation_level=None,
                timeout=self.busy_timeout_ms / 1000,
            )
        else:
            connection = sqlite3.connect(
                self.path,
                isolation_level=None,
                timeout=self.busy_timeout_ms / 1000,
            )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms:d}")
        if read_only:
            connection.execute("PRAGMA query_only = ON")
        else:
            journal_mode = str(
                connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]
            ).lower()
            if journal_mode != "wal":
                connection.close()
                raise PersistenceError(f"SQLite refused WAL mode (selected {journal_mode!r})")
            connection.execute("PRAGMA synchronous = FULL")
            connection.execute("PRAGMA wal_autocheckpoint = 1000")
            connection.execute("PRAGMA journal_size_limit = 67108864")
        if int(connection.execute("PRAGMA foreign_keys").fetchone()[0]) != 1:
            connection.close()
            raise PersistenceError("SQLite foreign-key enforcement could not be enabled")
        return connection

    @contextmanager
    def connection(self, *, read_only: bool = True) -> Iterator[sqlite3.Connection]:
        """Yield a configured connection and always close it.

        A writable connection is a low-level escape hatch for diagnostics. Normal
        mutations must use :meth:`transaction` so the single-writer invariant is
        enforced.
        """

        connection = self._open_connection(read_only=read_only)
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Yield one short, serialized, atomic write transaction."""

        path_key = os.path.normcase(str(self.path))
        active: set[str] = getattr(_WRITER_CONTEXT, "active_paths", set())
        if path_key in active:
            raise PersistenceError("nested write transactions are not supported")
        with self._writer_lock:
            active = set(active)
            active.add(path_key)
            _WRITER_CONTEXT.active_paths = active
            connection: sqlite3.Connection | None = None
            try:
                connection = self._open_connection(read_only=False)
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.commit()
            except BaseException:
                if connection is not None and connection.in_transaction:
                    connection.rollback()
                raise
            finally:
                if connection is not None:
                    connection.close()
                active.remove(path_key)
                _WRITER_CONTEXT.active_paths = active

    def initialize(self, *, backup_before_migration: bool = True) -> MigrationReport:
        """Create or migrate the project database, then verify its integrity."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        existed_with_data = self.path.is_file() and self.path.stat().st_size > 0
        with self._writer_lock:
            connection = self._open_connection(read_only=False)
            try:
                tables = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT name FROM sqlite_schema "
                        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                    )
                }
                if existed_with_data and tables and "schema_version" not in tables:
                    raise DatabaseNotInitializedError(
                        "existing SQLite database has no schema_version table; "
                        "refusing to guess or overwrite its schema"
                    )
                previous = current_schema_version(connection)
                supported = self.supported_schema_version
                # apply_migrations performs the authoritative newer-schema check.
                backup: Path | None = None
                if backup_before_migration and 0 < previous < supported:
                    backup = self._backup_connection(connection, previous)
                report = apply_migrations(
                    connection,
                    self.migrations_directory,
                    backup_path=str(backup) if backup is not None else None,
                )
            finally:
                connection.close()
        self.assert_integrity()
        return report

    def _backup_connection(self, source: sqlite3.Connection, version: int) -> Path:
        recovery_dir = self.path.parent / "recovery"
        recovery_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup = recovery_dir / f"{self.path.name}.schema-v{version}.{timestamp}.bak"
        destination = sqlite3.connect(backup)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
        # Windows requires a writable handle for FlushFileBuffers/os.fsync.
        with backup.open("r+b") as stream:
            os.fsync(stream.fileno())
        return backup

    def migration_history(self) -> tuple[MigrationInfo, ...]:
        with self.connection(read_only=True) as connection:
            return read_migration_history(connection)

    def verify_integrity(self, *, full: bool = True) -> IntegrityReport:
        pragma = "integrity_check" if full else "quick_check"
        with self.connection(read_only=True) as connection:
            messages = tuple(str(row[0]) for row in connection.execute(f"PRAGMA {pragma}"))
            violations = tuple(tuple(row) for row in connection.execute("PRAGMA foreign_key_check"))
        return IntegrityReport(
            database_ok=messages == ("ok",) and not violations,
            messages=messages,
            foreign_key_violations=violations,
        )

    def assert_integrity(self, *, full: bool = True) -> None:
        report = self.verify_integrity(full=full)
        if not report.database_ok:
            raise IntegrityCheckError(
                f"project database failed integrity validation: "
                f"messages={report.messages!r}, foreign_keys={report.foreign_key_violations!r}"
            )

    def checkpoint_wal(self, *, truncate: bool = False) -> tuple[int, int, int]:
        mode = "TRUNCATE" if truncate else "PASSIVE"
        with self._writer_lock, self.connection(read_only=False) as connection:
            row = connection.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()
        return int(row[0]), int(row[1]), int(row[2])

    def create_project(self, project: ProjectRecord) -> ProjectRecord:
        created_at = project.created_at or utc_now()
        updated_at = project.updated_at or created_at
        with self.transaction() as connection:
            connection.execute(
                "INSERT INTO projects("
                "id, name, source_language, settings_json, state, revision, created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    project.id,
                    project.name,
                    project.source_language,
                    _canonical_json(project.settings),
                    project.state,
                    project.revision,
                    created_at,
                    updated_at,
                ),
            )
        return ProjectRecord(
            id=project.id,
            name=project.name,
            source_language=project.source_language,
            settings=dict(project.settings),
            state=project.state,
            created_at=created_at,
            updated_at=updated_at,
            revision=project.revision,
        )

    def get_project(self, project_id: str) -> ProjectRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if row is None:
            return None
        return ProjectRecord(
            id=str(row["id"]),
            name=str(row["name"]),
            source_language=row["source_language"],
            settings=_load_json(row["settings_json"]),
            state=str(row["state"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            revision=int(row["revision"]),
        )

    def create_job(self, job: JobRecord, *, depends_on: Sequence[str] = ()) -> JobRecord:
        created_at = job.created_at or utc_now()
        updated_at = job.updated_at or created_at
        with self.transaction() as connection:
            connection.execute(
                "INSERT INTO jobs("
                "id, project_id, job_type, idempotency_key, state, priority, progress, "
                "scope_json, input_json, expected_output_json, resource_request_json, "
                "checkpoint_json, retry_count, max_retries, error_category, error_message, "
                "created_at, updated_at, started_at, completed_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job.id,
                    job.project_id,
                    job.job_type,
                    job.idempotency_key,
                    job.state.value,
                    job.priority,
                    job.progress,
                    _canonical_json(job.scope),
                    _canonical_json(job.inputs),
                    _canonical_json(job.expected_outputs),
                    _canonical_json(job.resource_request),
                    None if job.checkpoint is None else _canonical_json(job.checkpoint),
                    job.retry_count,
                    job.max_retries,
                    job.error_category,
                    job.error_message,
                    created_at,
                    updated_at,
                    job.started_at,
                    job.completed_at,
                ),
            )
            connection.executemany(
                "INSERT INTO job_dependencies(job_id, depends_on_job_id) VALUES (?, ?)",
                ((job.id, dependency) for dependency in depends_on),
            )
        values = {field: getattr(job, field) for field in job.__dataclass_fields__}
        values["created_at"] = created_at
        values["updated_at"] = updated_at
        return JobRecord(**values)

    def get_job(self, job_id: str) -> JobRecord | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return None if row is None else self._job_from_row(row)

    @staticmethod
    def _job_from_row(row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            id=str(row["id"]),
            project_id=str(row["project_id"]),
            job_type=str(row["job_type"]),
            idempotency_key=str(row["idempotency_key"]),
            state=JobState(row["state"]),
            priority=int(row["priority"]),
            progress=float(row["progress"]),
            scope=_load_json(row["scope_json"]),
            inputs=_load_json(row["input_json"]),
            expected_outputs=_load_json(row["expected_output_json"]),
            resource_request=_load_json(row["resource_request_json"]),
            checkpoint=None
            if row["checkpoint_json"] is None
            else _load_json(row["checkpoint_json"]),
            retry_count=int(row["retry_count"]),
            max_retries=int(row["max_retries"]),
            error_category=row["error_category"],
            error_message=row["error_message"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def transition_job(
        self,
        job_id: str,
        target: JobState,
        *,
        expected: JobState | None = None,
        progress: float | None = None,
        checkpoint: Mapping[str, Any] | None = None,
        error_category: str | None = None,
        error_message: str | None = None,
    ) -> JobRecord:
        if progress is not None and not 0.0 <= progress <= 1.0:
            raise ValueError("progress must be between zero and one")
        with self.transaction() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            current = JobState(row["state"])
            if expected is not None and current is not expected:
                raise InvalidStateTransitionError(
                    f"job {job_id} is {current.value}, expected {expected.value}"
                )
            transition_allowed = can_transition_job_status(
                DomainJobStatus(current.value.lower()),
                DomainJobStatus(target.value.lower()),
            )
            if target is not current and not transition_allowed:
                raise InvalidStateTransitionError(
                    f"job {job_id} cannot transition from {current.value} to {target.value}"
                )
            now = utc_now()
            started_at = row["started_at"]
            completed_at = row["completed_at"]
            if target is JobState.RUNNING and started_at is None:
                started_at = now
            if target in {JobState.CANCELLED, JobState.FAILED, JobState.SUCCEEDED}:
                completed_at = now
            connection.execute(
                "UPDATE jobs SET state = ?, progress = ?, checkpoint_json = ?, "
                "error_category = ?, error_message = ?, updated_at = ?, started_at = ?, "
                "completed_at = ? WHERE id = ?",
                (
                    target.value,
                    float(row["progress"]) if progress is None else progress,
                    row["checkpoint_json"] if checkpoint is None else _canonical_json(checkpoint),
                    error_category,
                    error_message,
                    now,
                    started_at,
                    completed_at,
                    job_id,
                ),
            )
            updated = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        assert updated is not None
        return self._job_from_row(updated)

    def recover_interrupted_jobs(self) -> tuple[str, ...]:
        """Make process-interrupted jobs terminal while preserving checkpoints."""

        recovered: list[str] = []
        with self.transaction() as connection:
            rows = connection.execute(
                "SELECT id, state FROM jobs WHERE state IN "
                "('PREPARING', 'RUNNING', 'PAUSING', 'CANCELLING') ORDER BY id"
            ).fetchall()
            now = utc_now()
            for row in rows:
                target = (
                    JobState.CANCELLED
                    if row["state"] == JobState.CANCELLING.value
                    else JobState.FAILED
                )
                connection.execute(
                    "UPDATE jobs SET state = ?, error_category = 'PROCESS_INTERRUPTED', "
                    "error_message = 'Application stopped before the job reached a checkpoint', "
                    "updated_at = ?, completed_at = ?, lease_owner = NULL, lease_expires_at = NULL "
                    "WHERE id = ?",
                    (target.value, now, now, row["id"]),
                )
                recovered.append(str(row["id"]))
        return tuple(recovered)

    def record_artifact(
        self,
        artifact: ArtifactRecord,
        *,
        source_artifact_ids: Sequence[str] = (),
    ) -> ArtifactRecord:
        created_at = artifact.created_at or utc_now()
        with self.transaction() as connection:
            connection.execute(
                "INSERT INTO artifacts("
                "id, project_id, sha256, byte_length, relative_path, logical_type, media_type, "
                "status, metadata_json, engine_id, engine_version, model_id, model_version, "
                "model_weight_sha256, parameters_json, prompt_version, provider_id, hardware_json, "
                "quality_metrics_json, seed, reproducibility_level, created_by, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    artifact.id,
                    artifact.project_id,
                    artifact.sha256,
                    artifact.byte_length,
                    artifact.relative_path,
                    artifact.logical_type,
                    artifact.media_type,
                    artifact.status.value,
                    _canonical_json(artifact.metadata),
                    artifact.engine_id,
                    artifact.engine_version,
                    artifact.model_id,
                    artifact.model_version,
                    artifact.model_weight_sha256,
                    _canonical_json(artifact.parameters),
                    artifact.prompt_version,
                    artifact.provider_id,
                    _canonical_json(artifact.hardware),
                    _canonical_json(artifact.quality_metrics),
                    artifact.seed,
                    artifact.reproducibility_level.value,
                    artifact.created_by,
                    created_at,
                ),
            )
            connection.executemany(
                "INSERT INTO artifact_dependencies("
                "artifact_id, source_artifact_id, dependency_role, ordinal"
                ") VALUES (?, ?, 'input', ?)",
                (
                    (artifact.id, source_id, ordinal)
                    for ordinal, source_id in enumerate(source_artifact_ids)
                ),
            )
        values = {field: getattr(artifact, field) for field in artifact.__dataclass_fields__}
        values["created_at"] = created_at
        return ArtifactRecord(**values)

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
        return None if row is None else self._artifact_from_row(row)

    def artifact_inventory(self, project_id: str) -> dict[str, int]:
        """Return content hashes and sizes expected by the artifact reconciler."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT sha256, byte_length FROM artifacts "
                "WHERE project_id = ? AND status <> 'QUARANTINED'",
                (project_id,),
            ).fetchall()
        return {str(row["sha256"]): int(row["byte_length"]) for row in rows}

    @staticmethod
    def _artifact_from_row(row: sqlite3.Row) -> ArtifactRecord:
        return ArtifactRecord(
            id=str(row["id"]),
            project_id=str(row["project_id"]),
            sha256=str(row["sha256"]),
            byte_length=int(row["byte_length"]),
            relative_path=str(row["relative_path"]),
            logical_type=str(row["logical_type"]),
            media_type=row["media_type"],
            status=ArtifactStatus(row["status"]),
            metadata=_load_json(row["metadata_json"]),
            engine_id=row["engine_id"],
            engine_version=row["engine_version"],
            model_id=row["model_id"],
            model_version=row["model_version"],
            model_weight_sha256=row["model_weight_sha256"],
            parameters=_load_json(row["parameters_json"]),
            prompt_version=row["prompt_version"],
            provider_id=row["provider_id"],
            hardware=_load_json(row["hardware_json"]),
            quality_metrics=_load_json(row["quality_metrics_json"]),
            seed=row["seed"],
            reproducibility_level=ReproducibilityLevel(row["reproducibility_level"]),
            created_by=row["created_by"],
            created_at=str(row["created_at"]),
        )

    def mark_artifact_status(self, artifact_id: str, status: ArtifactStatus) -> None:
        with self.transaction() as connection:
            cursor = connection.execute(
                "UPDATE artifacts SET status = ? WHERE id = ?", (status.value, artifact_id)
            )
            if cursor.rowcount != 1:
                raise KeyError(artifact_id)

    def append_audit_event(self, event: AuditEventRecord) -> AuditEventRecord:
        occurred_at = event.occurred_at or utc_now()
        with self.transaction() as connection:
            connection.execute(
                "INSERT INTO audit_events("
                "id, project_id, occurred_at, actor_type, actor_id, action, target_type, "
                "target_id, job_id, artifact_id, correlation_id, details_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.id,
                    event.project_id,
                    occurred_at,
                    event.actor_type,
                    event.actor_id,
                    event.action,
                    event.target_type,
                    event.target_id,
                    event.job_id,
                    event.artifact_id,
                    event.correlation_id,
                    _canonical_json(event.details),
                ),
            )
        values = {field: getattr(event, field) for field in event.__dataclass_fields__}
        values["occurred_at"] = occurred_at
        return AuditEventRecord(**values)

    def audit_events(self, project_id: str, *, limit: int = 1000) -> tuple[AuditEventRecord, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_events WHERE project_id = ? ORDER BY occurred_at, id LIMIT ?",
                (project_id, limit),
            ).fetchall()
        return tuple(
            AuditEventRecord(
                id=str(row["id"]),
                project_id=str(row["project_id"]),
                occurred_at=str(row["occurred_at"]),
                actor_type=str(row["actor_type"]),
                actor_id=row["actor_id"],
                action=str(row["action"]),
                target_type=row["target_type"],
                target_id=row["target_id"],
                job_id=row["job_id"],
                artifact_id=row["artifact_id"],
                correlation_id=row["correlation_id"],
                details=_load_json(row["details_json"]),
            )
            for row in rows
        )
